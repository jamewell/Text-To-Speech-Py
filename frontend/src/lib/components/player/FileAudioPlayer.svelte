<script lang="ts">
	import { onDestroy, onMount, tick } from 'svelte';
	import { api, type ApiError } from '$lib/api';
	import type { Chapter, FileDetail, ReadingHistory } from '$lib/schemas/api';

	const PROGRESS_SAVE_INTERVAL_MS = 15000;

	type SaveReason = 'pause' | 'seek' | 'chapter-change' | 'interval' | 'unload' | 'ended';

	export let file: FileDetail;

	let audioElement: HTMLAudioElement | null = null;
	let sortedChapters: Chapter[] = [];
	let unavailableChapterIds = new Set<number>();
	let currentChapterId: number | null = null;
	let audioUrl = '';
	let currentTime = 0;
	let duration = 0;
	let isPlaying = false;
	let isLoadingHistory = true;
	let isLoadingAudio = false;
	let playerError = '';
	let resumeMessage = '';
	let pendingSeekSeconds = 0;
	let historyRecord: ReadingHistory | null = null;
	let lastSavedPositionSeconds = -1;
	let lastSavedChapterId: number | null = null;
	let audioReloadAttempted = false;
	let progressTimer: ReturnType<typeof setInterval> | null = null;
	let unloadHandler: (() => void) | null = null;

	function chapterHasAudio(chapter: Chapter): boolean {
		return Boolean(chapter.audio_bucket_name && chapter.audio_object_name);
	}

	function isChapterMarkedUnavailable(chapterId: number): boolean {
		return unavailableChapterIds.has(chapterId);
	}

	function isChapterPlayable(chapter: Chapter): boolean {
		return chapterHasAudio(chapter) && !isChapterMarkedUnavailable(chapter.id);
	}

	function getCurrentChapter(): Chapter | null {
		return sortedChapters.find((chapter) => chapter.id === currentChapterId) ?? null;
	}

	function getPlayableChapters(): Chapter[] {
		return sortedChapters.filter((chapter) => isChapterPlayable(chapter));
	}

	function getChapterById(chapterId: number | null | undefined): Chapter | null {
		if (chapterId == null) {
			return null;
		}

		return sortedChapters.find((chapter) => chapter.id === chapterId) ?? null;
	}

	function getFirstPlayableChapter(): Chapter | null {
		return getPlayableChapters()[0] ?? null;
	}

	function getCurrentPlayableIndex(): number {
		const currentChapter = getCurrentChapter();
		if (!currentChapter) {
			return -1;
		}

		return getPlayableChapters().findIndex((chapter) => chapter.id === currentChapter.id);
	}

	function getPreviousPlayableChapter(): Chapter | null {
		const playableChapters = getPlayableChapters();
		const currentIndex = getCurrentPlayableIndex();
		if (currentIndex <= 0) {
			return null;
		}

		return playableChapters[currentIndex - 1] ?? null;
	}

	function getNextPlayableChapter(): Chapter | null {
		const playableChapters = getPlayableChapters();
		const currentIndex = getCurrentPlayableIndex();
		if (currentIndex < 0 || currentIndex >= playableChapters.length - 1) {
			return null;
		}

		return playableChapters[currentIndex + 1] ?? null;
	}

	function formatTime(value: number): string {
		if (!Number.isFinite(value) || value < 0) {
			return '00:00';
		}

		const totalSeconds = Math.floor(value);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;

		return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
	}

	async function persistProgress(reason: SaveReason): Promise<void> {
		const currentChapter = getCurrentChapter();
		if (!audioElement || !currentChapter) {
			return;
		}

		const positionSeconds = Number.isFinite(audioElement.currentTime) ? audioElement.currentTime : currentTime;
		const roundedPosition = Number(positionSeconds.toFixed(2));

		if (
			reason === 'interval' &&
			lastSavedChapterId === currentChapter.id &&
			Math.abs(lastSavedPositionSeconds - roundedPosition) < 5
		) {
			return;
		}

		try {
			const record = await api.upsertHistory(file.id, {
				chapter_id: currentChapter.id,
				position_seconds: roundedPosition
			});
			historyRecord = record;
			lastSavedChapterId = record.chapter_id ?? null;
			lastSavedPositionSeconds = record.position_seconds;
		} catch (error) {
			const apiError = error as ApiError;
			if (!apiError.isAuthError && reason !== 'interval') {
				playerError = apiError.message || 'Failed to save listening progress.';
			}
		}
	}

	async function loadChapterAudio(
		chapter: Chapter,
		seekSeconds: number = 0,
		autoplay: boolean = false
	): Promise<void> {
		if (!chapterHasAudio(chapter)) {
			playerError = 'Audio is not available for this chapter yet.';
			audioUrl = '';
			currentChapterId = chapter.id;
			currentTime = 0;
			duration = 0;
			isPlaying = false;
			return;
		}

		isLoadingAudio = true;
		playerError = '';
		resumeMessage = '';
		pendingSeekSeconds = seekSeconds;
		audioReloadAttempted = false;

		try {
			const response = await api.getChapterAudio(chapter.id);
			currentChapterId = chapter.id;
			audioUrl = response.url;
			currentTime = seekSeconds;
			duration = 0;

			if (audioElement) {
				audioElement.pause();
				await tick();
				audioElement.load();
			}

			if (autoplay) {
				queueMicrotask(async () => {
					try {
						await audioElement?.play();
					} catch {
						isPlaying = false;
					}
				});
			}
		} catch (error) {
			const apiError = error as ApiError;
			currentChapterId = chapter.id;
			audioUrl = '';
			currentTime = seekSeconds;
			duration = 0;
			isPlaying = false;

			if (apiError.status === 409) {
				unavailableChapterIds = new Set([...unavailableChapterIds, chapter.id]);
				playerError = 'Audio for this chapter is not available yet.';
			} else {
				playerError = apiError.message || 'Failed to load chapter audio.';
			}
		} finally {
			isLoadingAudio = false;
		}
	}

	async function selectChapter(
		chapter: Chapter,
		options: {
			seekSeconds?: number;
			autoplay?: boolean;
			saveCurrent?: boolean;
		} = {}
	): Promise<void> {
		const { seekSeconds = 0, autoplay = false, saveCurrent = true } = options;

		if (saveCurrent && currentChapterId !== null && currentChapterId !== chapter.id) {
			await persistProgress('chapter-change');
		}

		await loadChapterAudio(chapter, seekSeconds, autoplay);
	}

	async function loadResumeState(): Promise<void> {
		sortedChapters = [...file.chapters].sort((a, b) => a.chapter_index - b.chapter_index);
		const firstPlayableChapter = getFirstPlayableChapter();

		if (!firstPlayableChapter) {
			isLoadingHistory = false;
			playerError = 'This file has no playable chapters yet.';
			return;
		}

		try {
			const history = await api.getHistory(1, 100);
			historyRecord = history.history.find((record) => record.file_id === file.id) ?? null;
		} catch (error) {
			const apiError = error as ApiError;
			if (!apiError.isAuthError) {
				playerError = apiError.message || 'Failed to load listening history.';
			}
		}

		const savedChapter = getChapterById(historyRecord?.chapter_id);
		const canResumeSavedChapter = savedChapter && isChapterPlayable(savedChapter);

		if (canResumeSavedChapter) {
			const seekSeconds = historyRecord?.position_seconds ?? 0;
			resumeMessage =
				seekSeconds > 0
					? `Resumed from ${formatTime(seekSeconds)} in ${savedChapter.title}.`
					: `Opened ${savedChapter.title}.`;
			await selectChapter(savedChapter, {
				seekSeconds,
				autoplay: false,
				saveCurrent: false
			});
		} else {
			if (historyRecord?.chapter_id != null) {
				resumeMessage = 'Saved chapter audio is unavailable, so playback starts from the first available chapter.';
			}
			await selectChapter(firstPlayableChapter, {
				seekSeconds: 0,
				autoplay: false,
				saveCurrent: false
			});
		}

		isLoadingHistory = false;
	}

	async function togglePlayback(): Promise<void> {
		if (!audioElement || !audioUrl) {
			return;
		}

		if (audioElement.paused) {
			try {
				await audioElement.play();
			} catch {
				playerError = 'Playback could not be started.';
			}
			return;
		}

		audioElement.pause();
	}

	async function goToPreviousChapter(): Promise<void> {
		const previousChapter = getPreviousPlayableChapter();
		if (!previousChapter) {
			return;
		}

		await selectChapter(previousChapter, { autoplay: true });
	}

	async function goToNextChapter(): Promise<void> {
		const nextChapter = getNextPlayableChapter();
		if (!nextChapter) {
			await persistProgress('ended');
			isPlaying = false;
			return;
		}

		await selectChapter(nextChapter, { autoplay: true });
	}

	function handleLoadedMetadata(): void {
		if (!audioElement) {
			return;
		}

		duration = Number.isFinite(audioElement.duration) ? audioElement.duration : 0;

		if (pendingSeekSeconds > 0) {
			audioElement.currentTime = Math.min(pendingSeekSeconds, duration || pendingSeekSeconds);
			currentTime = audioElement.currentTime;
			pendingSeekSeconds = 0;
		}
	}

	function handleTimeUpdate(): void {
		if (!audioElement) {
			return;
		}

		currentTime = audioElement.currentTime;
		if (Number.isFinite(audioElement.duration)) {
			duration = audioElement.duration;
		}
	}

	async function handleSeek(event: Event): Promise<void> {
		if (!audioElement) {
			return;
		}

		const input = event.currentTarget as HTMLInputElement;
		const nextTime = Number(input.value);
		audioElement.currentTime = nextTime;
		currentTime = nextTime;
		await persistProgress('seek');
	}

	function handlePlay(): void {
		isPlaying = true;
	}

	async function handlePause(): Promise<void> {
		isPlaying = false;
		await persistProgress('pause');
	}

	async function handleEnded(): Promise<void> {
		isPlaying = false;
		await goToNextChapter();
	}

	async function handleAudioError(): Promise<void> {
		const currentChapter = getCurrentChapter();
		if (!currentChapter) {
			return;
		}

		if (!audioReloadAttempted) {
			audioReloadAttempted = true;
			await loadChapterAudio(currentChapter, currentTime, isPlaying);
			return;
		}

		playerError = 'Audio playback failed. Try reloading this chapter.';
		isPlaying = false;
	}

	onMount(() => {
		void loadResumeState();

		progressTimer = setInterval(() => {
			if (isPlaying) {
				void persistProgress('interval');
			}
		}, PROGRESS_SAVE_INTERVAL_MS);

		unloadHandler = () => {
			void persistProgress('unload');
		};

		window.addEventListener('beforeunload', unloadHandler);
	});

	onDestroy(() => {
		if (progressTimer) {
			clearInterval(progressTimer);
		}

		if (unloadHandler) {
			window.removeEventListener('beforeunload', unloadHandler);
		}

		void persistProgress('unload');
	});
</script>

<div class="space-y-6">
	<div class="card">
		<div class="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
			<div>
				<p class="text-sm font-medium text-blue-700">Audio Player</p>
				<h2 class="mt-1 text-2xl font-bold text-gray-900">{file.original_filename}</h2>
				<p class="mt-2 text-sm text-gray-500">
					{sortedChapters.length} chapters • {formatFileSize(file.file_size)} • {file.visibility}
				</p>
			</div>
			<div class="rounded-lg bg-gray-100 px-4 py-3 text-sm text-gray-600">
				<p class="font-medium text-gray-900">Status</p>
				<p class="capitalize">{file.status}</p>
			</div>
		</div>

		{#if isLoadingHistory}
			<div class="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
				Loading your playback state...
			</div>
		{:else if resumeMessage}
			<div class="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
				{resumeMessage}
			</div>
		{/if}

		{#if playerError}
			<div class="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
				{playerError}
			</div>
		{/if}

		<div class="mt-6 rounded-xl bg-gray-950 p-5 text-white">
			<div class="mb-4 flex flex-col gap-2">
				<p class="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">Now Playing</p>
				<h3 class="text-xl font-semibold">
					{getCurrentChapter()?.title ?? 'Select a chapter'}
				</h3>
				<p class="text-sm text-gray-300">
					{#if getCurrentChapter()}
						Chapter {getCurrentChapter()?.chapter_index}
					{:else}
						No chapter selected
					{/if}
				</p>
			</div>

			<audio
				bind:this={audioElement}
				src={audioUrl}
				preload="metadata"
				on:loadedmetadata={handleLoadedMetadata}
				on:timeupdate={handleTimeUpdate}
				on:play={handlePlay}
				on:pause={handlePause}
				on:ended={handleEnded}
				on:error={handleAudioError}
			></audio>

			<div class="flex flex-wrap items-center gap-3">
				<button
					class="rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
					on:click={goToPreviousChapter}
					disabled={!getPreviousPlayableChapter() || isLoadingAudio}
				>
					Previous
				</button>
				<button
					class="rounded-full bg-blue-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-40"
					on:click={togglePlayback}
					disabled={!audioUrl || isLoadingAudio}
				>
					{#if isLoadingAudio}
						Loading...
					{:else if isPlaying}
						Pause
					{:else}
						Play
					{/if}
				</button>
				<button
					class="rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
					on:click={goToNextChapter}
					disabled={!getNextPlayableChapter() || isLoadingAudio}
				>
					Next
				</button>
			</div>

			<div class="mt-5">
				<input
					type="range"
					min="0"
					max={duration || 0}
					step="0.1"
					value={currentTime}
					on:change={handleSeek}
					class="h-2 w-full cursor-pointer appearance-none rounded-lg bg-white/20"
					disabled={!audioUrl || duration <= 0}
					aria-label="Playback progress"
				/>
				<div class="mt-2 flex items-center justify-between text-xs text-gray-300">
					<span>{formatTime(currentTime)}</span>
					<span>{formatTime(duration)}</span>
				</div>
			</div>
		</div>
	</div>

	<div class="card">
		<div class="mb-4 flex items-center justify-between">
			<div>
				<h3 class="text-xl font-semibold text-gray-900">Chapters</h3>
				<p class="text-sm text-gray-500">Choose a chapter to start playback.</p>
			</div>
		</div>

		<div class="space-y-3">
			{#each sortedChapters as chapter (chapter.id)}
				{@const isSelected = chapter.id === currentChapterId}
				{@const hasAudio = chapterHasAudio(chapter)}
				{@const isUnavailable = isChapterMarkedUnavailable(chapter.id)}
				<button
					class={`w-full rounded-xl border p-4 text-left transition ${
						isSelected
							? 'border-blue-300 bg-blue-50'
							: 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
					} ${!hasAudio || isUnavailable ? 'opacity-70' : ''}`}
					on:click={() => selectChapter(chapter, { autoplay: true })}
					disabled={!hasAudio || isUnavailable || isLoadingAudio}
				>
					<div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
						<div>
							<p class="text-sm font-medium text-blue-700">Chapter {chapter.chapter_index}</p>
							<h4 class="text-base font-semibold text-gray-900">{chapter.title}</h4>
							<p class="mt-1 text-sm text-gray-500">
								Pages {chapter.start_page}-{chapter.end_page}
							</p>
						</div>
						<div class="text-sm">
							{#if isSelected}
								<span class="rounded-full bg-blue-100 px-3 py-1 font-medium text-blue-700">
									Selected
								</span>
							{:else if isUnavailable}
								<span class="rounded-full bg-red-100 px-3 py-1 font-medium text-red-700">
									Unavailable
								</span>
							{:else if hasAudio}
								<span class="rounded-full bg-green-100 px-3 py-1 font-medium text-green-700">
									Ready
								</span>
							{:else}
								<span class="rounded-full bg-yellow-100 px-3 py-1 font-medium text-yellow-700">
									Processing
								</span>
							{/if}
						</div>
					</div>
				</button>
			{/each}
		</div>
	</div>
</div>

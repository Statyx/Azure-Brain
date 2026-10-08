
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import type { Choice, Message, PersonRef, Scenario, ScenarioOption, SourceRef, ThinkingStep, CoworkTaskStatus } from "../types/scenario";
import { IconAssistant, IconChat, IconChevronDown, IconEdit, IconFolder, IconGrid, IconInfo, IconLibrary, IconMenu, IconMic, IconMore, IconPlus, IconSearch, IconSettings, IconShield, IconSparkle, IconTasks, IconWave } from "./icons";
import { DEFAULT_DEMO_PROFILE, DemoProfile, getProfileServerSnapshot, getProfileSnapshot, nameInitials, profileTokens, resolveTokens, storeProfile, subscribeProfile } from "./profile";
import { AgentAvatar, ApprovalPolicyModal, CoworkTaskView, EmailDraftCard, getIdentity, IconClose, MessageActionBar, PersonCard, renderDraftWithMention, renderMarkdown, ReportChartCard, ReportView, ScenarioCarousel, SourceChips, SourcePanel } from "./cards";
/* ---------- Page ---------- */

export default function PlaygroundShell({ scenario }: { scenario: Scenario }) {
  // Everything scenario-specific is destructured here so the rest of the component reads the
  // same names it did when the data was imported from a module. The engine knows the shape of a
  // scenario, never its contents.
  const pinnedAgents = scenario.agents;
  const { conversationHistory, suggestedChips, upcomingTasks: coworkUpcomingTasks, tryThese: coworkTryThese } = scenario.shell;
  const tracks = scenario.tracks;
  const primaryTrackId = tracks[0].id;
const scenes = tracks[0].scenes;
  const veloaEvents = scenario.coworkSession?.events ?? [];
  const veloaTasks = scenario.coworkSession?.tasks ?? [];
  const veloaSkillsUsed = scenario.coworkSession?.skillsUsed ?? [];
  const approverAuthorizationStatus = scenario.artifacts?.authorization;

  const [viewMode, setViewMode] = useState<"conversation" | "cowork">("conversation");
  const [activeTrack, setActiveTrack] = useState<string>(primaryTrackId);
  const [started, setStarted] = useState(false);
  const [sceneIndex, setSceneIndex] = useState(0);
  // Mirrors sceneIndex synchronously so chainNext can always read the true current index even
  // when multiple auto-advance hops fire back-to-back through nested setTimeout closures (where
  // the `sceneIndex` closure variable captured at schedule-time would otherwise go stale and
  // cause the same scene to be re-triggered in a loop).
  const sceneIndexRef = useRef(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draftText, setDraftText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [processingStep, setProcessingStep] = useState<ThinkingStep | null>(null);
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [assistantDraft, setAssistantDraft] = useState("");
  const [pendingChoice, setPendingChoice] = useState<Choice | null>(null);
  const [selectedSource, setSelectedSource] = useState<SourceRef | null>(null);
  const [mentionMenuOpen, setMentionMenuOpen] = useState(false);
  const [mentionHint, setMentionHint] = useState<string | null>(null);
  const [mentionTarget, setMentionTarget] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [emailSending, setEmailSending] = useState(false);
  const [activePerson, setActivePerson] = useState<PersonRef | null>(null);
  const [, setFollowupTopic] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  // Demo profile (operator + approver), persisted in localStorage and read through a small
  // external store so hydration stays consistent with the server render.
  const profile = useSyncExternalStore(subscribeProfile, getProfileSnapshot, getProfileServerSnapshot);
  const [profileDraft, setProfileDraft] = useState<DemoProfile>(DEFAULT_DEMO_PROFILE);
  const [profileError, setProfileError] = useState("");

  const tokens = useMemo(() => profileTokens(profile), [profile]);
  const userFullName = tokens.userName;

  const [approvalPolicyOpen, setApprovalPolicyOpen] = useState(false);

  const saveProfile = () => {
    const trimmed: DemoProfile = {
      user: {
        firstName: profileDraft.user.firstName.trim() || DEFAULT_DEMO_PROFILE.user.firstName,
        lastName: profileDraft.user.lastName.trim() || DEFAULT_DEMO_PROFILE.user.lastName,
        photo: profileDraft.user.photo.trim() || DEFAULT_DEMO_PROFILE.user.photo,
      },
      approver: {
        firstName: profileDraft.approver.firstName.trim() || DEFAULT_DEMO_PROFILE.approver.firstName,
        lastName: profileDraft.approver.lastName.trim() || DEFAULT_DEMO_PROFILE.approver.lastName,
        title: profileDraft.approver.title.trim() || DEFAULT_DEMO_PROFILE.approver.title,
      },
    };
    const persisted = storeProfile(trimmed);
    setProfileError(persisted ? "" : "Profile applied for this session only \u2014 browser storage is full.");
    setSettingsOpen(false);
  };

  // Reads the picked image as a data URL so the demo operator can use a local photo without
  // deploying it to /public. Kept small to stay within the localStorage quota.
  const handlePhotoUpload = (file: File | undefined) => {
    if (!file) return;
    if (file.size > 1_500_000) {
      setProfileError("Photo is too large (max 1.5 MB). Use a smaller image or paste a URL.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setProfileError("");
      setProfileDraft((prev) => ({ ...prev, user: { ...prev.user, photo: String(reader.result) } }));
    };
    reader.readAsDataURL(file);
  };

  // Cowork task session (Veloa Performance GTM replay) \u2014 fully separate from the
  // Conversation-mode state above.
  const [coworkTaskOpen, setCoworkTaskOpen] = useState(false);
  const [coworkEventIdx, setCoworkEventIdx] = useState(0);
  const [coworkStatus, setCoworkStatus] = useState<"running" | "complete">("running");
  const [coworkTaskStatus, setCoworkTaskStatus] = useState<Record<number, CoworkTaskStatus>>({
    1: "pending",
    2: "pending",
    3: "pending",
    4: "pending",
  });

  const typingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sendTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const thinkingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const assistantTypingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const assistantPauseRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mentionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mentionIntroducedRef = useRef(false);
  const pendingMentionRef = useRef<(() => void) | null>(null);
  const scenarioAutoAdvanceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Holds the choice currently being typed, so the composer's send timeout always commits the right one.
  const pendingChoiceCommitRef = useRef<Choice | null>(null);
  // A proactive step unlocked by the previous one waits here as the only suggested reply, so the
  // presenter paces every transition (see known_issues.md #31).
  const [awaitingStep, setAwaitingStep] = useState<Choice | null>(null);
  const conversationRef = useRef<HTMLDivElement | null>(null);

  const scenesData = useMemo(
    () => resolveTokens((tracks.find((t) => t.id === activeTrack) ?? tracks[0]).scenes, tokens),
    [tracks, activeTrack, tokens]
  );
  const isFinished = sceneIndex >= scenesData.length;
  const isBusy = isTyping || processingStep !== null || isAssistantTyping || mentionMenuOpen;

  const currentChoices = useMemo(() => {
    if (!started || isFinished) return [];
    return scenesData[sceneIndex].choices;
  }, [started, isFinished, sceneIndex, scenesData]);

  const visibleChoices = useMemo(
    () => (awaitingStep ? [awaitingStep] : currentChoices.filter((c) => !c.autoTriggerOnly)),
    [currentChoices, awaitingStep]
  );

  // Keeps the newest content in view while a turn plays out (typing, thinking steps, the answer and
  // its cards), so the presenter never scrolls by hand mid-answer. Once the turn is done nothing
  // changes, so scrolling back up to walk through the result stays free.
  useEffect(() => {
    const el = conversationRef.current;
    if (!el) return;
    const frame = requestAnimationFrame(() => {
      if (typeof el.scrollTo === "function") {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      } else {
        el.scrollTop = el.scrollHeight;
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [messages.length, processingStep, isAssistantTyping, emailSending, awaitingStep, selectedScenarioId]);

  useEffect(() => {
    const el = conversationRef.current;
    if (!el || !isAssistantTyping) return;
    el.scrollTop = el.scrollHeight;
  }, [assistantDraft, isAssistantTyping]);

  const clearAllTimers = () => {
    if (typingRef.current) {
      clearInterval(typingRef.current);
      typingRef.current = null;
    }
    if (sendTimeoutRef.current) {
      clearTimeout(sendTimeoutRef.current);
      sendTimeoutRef.current = null;
    }
    if (thinkingRef.current) {
      clearInterval(thinkingRef.current);
      thinkingRef.current = null;
    }
    if (assistantTypingRef.current) {
      clearInterval(assistantTypingRef.current);
      assistantTypingRef.current = null;
    }
    if (assistantPauseRef.current) {
      clearTimeout(assistantPauseRef.current);
      assistantPauseRef.current = null;
    }
    if (mentionTimeoutRef.current) {
      clearTimeout(mentionTimeoutRef.current);
      mentionTimeoutRef.current = null;
    }
    pendingMentionRef.current = null;
    if (scenarioAutoAdvanceRef.current) {
      clearTimeout(scenarioAutoAdvanceRef.current);
      scenarioAutoAdvanceRef.current = null;
    }
  };

  useEffect(() => clearAllTimers, []);

  const commitAssistantMessage = (choice: Choice) => {
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: choice.assistant,
        chain: choice.chain,
        mention: choice.mention,
        report: choice.report,
        chart: choice.chart,
        reflection: choice.reflection,
        sources: choice.sources,
        scenarios: choice.scenarios,
        person: choice.person,
        emailDraft: choice.emailDraft,
      },
    ]);
    if (choice.person) setActivePerson(choice.person);
    if (choice.followupTopic) setFollowupTopic(choice.followupTopic);
    const nextIndex = sceneIndexRef.current + 1;
    sceneIndexRef.current = nextIndex;
    setSceneIndex(nextIndex);
    setPendingChoice(null);

    if (choice.chainNext) {
      // This step hands off to the next agent. The hand-off is offered as the next suggested reply
      // rather than played on its own, so the presenter paces every step. Reads scenesData via sceneIndexRef
      // (not the possibly-stale `sceneIndex` closure variable) so back-to-back chained hops each
      // resolve the true current scene instead of looping on the same one.
      const nextScene = scenesData[nextIndex];
      const nextChoice = nextScene?.choices.find((c) => c.autoTriggerOnly);
      if (nextChoice) setAwaitingStep(nextChoice);
    }
  };

  const beginAssistantReveal = (choice: Choice) => {
    if (choice.report || !choice.assistant) {
      // Structured reports render fully formatted \u2014 skip the character-by-character reveal.
      commitAssistantMessage(choice);
      return;
    }
    setIsAssistantTyping(true);
    setAssistantDraft("");
    const full = choice.assistant;
    let i = 0;
    // Slow, readable reveal: small chunk of characters per tick, roughly ~110 ticks regardless of length.
    const step = Math.max(1, Math.round(full.length / 110));
    assistantTypingRef.current = setInterval(() => {
      i += step;
      if (i >= full.length) {
        if (assistantTypingRef.current) {
          clearInterval(assistantTypingRef.current);
          assistantTypingRef.current = null;
        }
        setAssistantDraft(full);
        assistantPauseRef.current = setTimeout(() => {
          commitAssistantMessage(choice);
          setIsAssistantTyping(false);
          setAssistantDraft("");
        }, 500);
        return;
      }
      setAssistantDraft(full.slice(0, i));
    }, 45);
  };

  const beginThinking = (choice: Choice) => {
    const steps =
      choice.thinkingSteps && choice.thinkingSteps.length
        ? choice.thinkingSteps
        : [{ label: `Consulting ${choice.chain}`, sub: "Retrieving the data needed to answer accurately." }];
    let idx = 0;
    setProcessingStep(steps[0]);
    // Chained timeouts so each step can set its own on-screen duration (durationMs).
    const next = () => {
      idx += 1;
      if (idx >= steps.length) {
        thinkingRef.current = null;
        setProcessingStep(null);
        beginAssistantReveal(choice);
        return;
      }
      setProcessingStep(steps[idx]);
      thinkingRef.current = setTimeout(next, steps[idx].durationMs ?? 1400);
    };
    thinkingRef.current = setTimeout(next, steps[0].durationMs ?? 1400);
  };

  // Sends the prepared email draft ("Send" button inside the EmailDraftCard) and confirms delivery.
  const sendEmailAndNotify = () => {
    if (emailSent || isBusy) return;
    setEmailSent(true);
    setEmailSending(true);

    const name = activePerson?.name ?? "the approver";

    const steps: ThinkingStep[] = [
      {
        label: "Sending the email",
        sub: `Delivering the email to ${name} via WorkIQ.`,
      },
    ];
    let idx = 0;
    setProcessingStep(steps[0]);
    thinkingRef.current = setInterval(() => {
      idx += 1;
      if (idx >= steps.length) {
        if (thinkingRef.current) {
          clearInterval(thinkingRef.current);
          thinkingRef.current = null;
        }
        setProcessingStep(null);
        setEmailSending(false);

        const full = `\u2705 Email sent to ${name}.`;
        setIsAssistantTyping(true);
        setAssistantDraft("");
        let i = 0;
        const step = Math.max(1, Math.round(full.length / 110));
        assistantTypingRef.current = setInterval(() => {
          i += step;
          if (i >= full.length) {
            if (assistantTypingRef.current) {
              clearInterval(assistantTypingRef.current);
              assistantTypingRef.current = null;
            }
            setAssistantDraft(full);
            assistantPauseRef.current = setTimeout(() => {
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  text: full,
                  chain: "Compliance Agent \u2022 WorkIQ",
                  mention: "CaldovaIQ",
                  sources: [
                    {
                      id: "email-sent-log",
                      label: "WorkIQ \u2014 email log",
                      system: "governance",
                      detail: `WorkIQ \u2014 delivery log for the email sent to ${name}${activePerson?.title ? `, ${activePerson.title}` : ""}.`,
                    },
                  ],
                },
              ]);
              setIsAssistantTyping(false);
              setAssistantDraft("");
            }, 500);
            return;
          }
          setAssistantDraft(full.slice(0, i));
        }, 45);
        return;
      }
      setProcessingStep(steps[idx]);
    }, 1400);
  };

  const viewApprovalPolicy = () => setApprovalPolicyOpen(true);
  const closeApprovalPolicy = () => setApprovalPolicyOpen(false);

  const commitUserMessage = (choice: Choice) => {
    setStarted(true);
    setMessages((prev) => [...prev, { role: "user", text: choice.user, mention: choice.mention }]);
  };

  const typeComposerText = (full: string, prefixLen: number) => {
    let i = prefixLen;
    typingRef.current = setInterval(() => {
      i += 1;
      if (i >= full.length) {
        if (typingRef.current) {
          clearInterval(typingRef.current);
          typingRef.current = null;
        }
        setDraftText(full);
        sendTimeoutRef.current = setTimeout(() => {
          const choice = pendingChoiceCommitRef.current;
          if (!choice) return;
          commitUserMessage(choice);
          setIsTyping(false);
          setDraftText("");
          beginThinking(choice);
        }, 600);
        return;
      }
      setDraftText(full.slice(0, i));
    }, 32);
  };

  const startTyping = (choice: Choice) => {
    if (isBusy) return;
    clearAllTimers();
    setAwaitingStep(null);
    // Drop focus from the clicked control so a stray Space/Enter can never launch the next step.
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    setPendingChoice(choice);
    pendingChoiceCommitRef.current = choice;

    if (choice.proactive) {
      // No user-typed message for this turn \u2014 it plays as a system notification straight into "thinking".
      beginThinking(choice);
      return;
    }

    setIsTyping(true);
    setDraftText("");

    if (choice.mention && !mentionIntroducedRef.current) {
      // First time we mention an agent: show the "@" trigger and the agent picker before typing the rest.
      mentionIntroducedRef.current = true;
      setDraftText("@");
      setMentionHint(choice.chain ?? null);
      setMentionTarget(choice.mention);
      setMentionMenuOpen(true);
      // Presenter-paced: the picker stays open until "Continue" is clicked.
      pendingMentionRef.current = () => {
        setMentionMenuOpen(false);
        const prefixed = `@${choice.mention} ${choice.user}`;
        setDraftText(`@${choice.mention} `);
        typeComposerText(prefixed, `@${choice.mention} `.length);
      };
      return;
    }

    if (choice.mention) {
      const prefixed = `@${choice.mention} ${choice.user}`;
      setDraftText(`@${choice.mention} `);
      typeComposerText(prefixed, `@${choice.mention} `.length);
      return;
    }

    typeComposerText(choice.user, 0);
  };

  const handleScenarioSelect = (scenario: ScenarioOption) => {
    if (isBusy || selectedScenarioId) return;
    if (scenario.id !== "recommended") {
      // A non-recommended pick gets a grounded, out-of-band reply that steers back to the
      // recommended option. The carousel stays clickable so the presenter can recover.
      if (!scenario.response) {
        setSelectedScenarioId(scenario.id);
        return;
      }
      const full = scenario.response;
      const mention = [...messages].reverse().find((m) => m.scenarios)?.mention ?? "CaldovaIQ";
      setIsAssistantTyping(true);
      setAssistantDraft("");
      let i = 0;
      const step = Math.max(1, Math.round(full.length / 110));
      assistantTypingRef.current = setInterval(() => {
        i += step;
        if (i < full.length) {
          setAssistantDraft(full.slice(0, i));
          return;
        }
        if (assistantTypingRef.current) {
          clearInterval(assistantTypingRef.current);
          assistantTypingRef.current = null;
        }
        setAssistantDraft(full);
        assistantPauseRef.current = setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", text: full, mention, sources: scenario.responseSources },
          ]);
          setIsAssistantTyping(false);
          setAssistantDraft("");
        }, 400);
      }, 30);
      return;
    }
    setSelectedScenarioId(scenario.id);
    // Selecting the recommended scenario unlocks the proactive follow-up (governance review, or
    // looping in the owner). It is offered as the next suggested reply and plays on click only.
    const nextChoice = currentChoices.find((c) => c.autoTriggerOnly);
    if (nextChoice) setAwaitingStep(nextChoice);
  };

  const continueMention = () => {
    const fn = pendingMentionRef.current;
    pendingMentionRef.current = null;
    fn?.();
  };

  const resetDemo = () => {
    clearAllTimers();
    setIsTyping(false);
    setDraftText("");
    setProcessingStep(null);
    setIsAssistantTyping(false);
    setAssistantDraft("");
    setPendingChoice(null);
    setSelectedSource(null);
    setMentionMenuOpen(false);
    setMentionTarget(null);
    setSelectedScenarioId(null);
    setMobileSidebarOpen(false);
    setEmailSent(false);
    setEmailSending(false);
    setActivePerson(null);
    setFollowupTopic("");
    setApprovalPolicyOpen(false);
    mentionIntroducedRef.current = false;
    pendingChoiceCommitRef.current = null;
    setAwaitingStep(null);
    setStarted(false);
    setSceneIndex(0);
    sceneIndexRef.current = 0;
    setMessages([]);
    setActiveTrack(primaryTrackId);
  };

  // Launches the Cowork task session for the Veloa Performance GTM replay. This stays entirely
  // inside the Cowork screen \u2014 it does not touch Conversation-mode state, scenes, or CaldovaIQ chat.
  const startCoworkTask = () => {
    setCoworkEventIdx(0);
    setCoworkStatus("running");
    setCoworkTaskStatus({ 1: "pending", 2: "pending", 3: "pending", 4: "pending" });
    setCoworkTaskOpen(true);
  };

  const closeCoworkTask = () => {
    setCoworkTaskOpen(false);
    setCoworkEventIdx(0);
    setCoworkStatus("running");
    setCoworkTaskStatus({ 1: "pending", 2: "pending", 3: "pending", 4: "pending" });
  };

  // Auto-advances through the scripted events array \u2014 fully autonomous, no pauses for
  // user input, matching the one-shot prompt in the Veloa Performance spec.
  useEffect(() => {
    if (!coworkTaskOpen || coworkStatus !== "running") return;
    const event = veloaEvents[coworkEventIdx];
    if (!event) return;
    const timer = setTimeout(() => {
      if (event.kind === "taskUpdate") {
        setCoworkTaskStatus((prev) => ({ ...prev, [event.taskId]: event.status }));
      }
      if (coworkEventIdx + 1 >= veloaEvents.length) {
        setCoworkStatus("complete");
      } else {
        setCoworkEventIdx((idx) => idx + 1);
      }
    }, event.duration);
    return () => clearTimeout(timer);
  }, [coworkTaskOpen, coworkStatus, coworkEventIdx]);

  return (
    <div className="h-full flex flex-col overflow-hidden">

      <div className="flex-1 min-h-0 flex md:items-start md:justify-center md:px-4 md:py-4">
        <div className="relative w-full flex-1 md:flex-none min-h-0 md:h-[min(860px,calc(100dvh-7rem))] md:max-w-[1400px] md:rounded-xl md:border md:border-hairline bg-white md:shadow-2xl overflow-hidden flex">
          {/* Mobile sidebar backdrop */}
          {mobileSidebarOpen && (
            <div
              className="fixed inset-0 z-30 bg-black/30 md:hidden"
              onClick={() => setMobileSidebarOpen(false)}
              aria-hidden
            />
          )}

          {/* Sidebar */}
          <aside
            className={`fixed inset-y-0 left-0 z-40 w-[85%] max-w-[300px] border-r border-hairline flex flex-col bg-white transition-transform duration-300 ease-out ${
              mobileSidebarOpen ? "translate-x-0" : "-translate-x-full"
            } md:static md:z-auto md:w-[290px] md:shrink-0 md:translate-x-0 md:transition-none`}
          >
            <div className="flex items-center gap-3 px-4 pt-4 pb-2 text-ink-muted">
              <button
                type="button"
                onClick={() => setMobileSidebarOpen(false)}
                className="md:pointer-events-none"
                aria-label="Close menu"
              >
                <IconMenu />
              </button>
              <IconGrid />
            </div>

            <div className="px-4 pt-2 flex items-center gap-6 text-sm">
              <button
                type="button"
                onClick={() => setViewMode("conversation")}
                className={
                  viewMode === "conversation"
                    ? "font-semibold text-ink border-b-2 border-ink pb-2"
                    : "text-ink-muted pb-2 hover:text-ink"
                }
              >
                Conversation
              </button>
              <button
                type="button"
                onClick={() => setViewMode("cowork")}
                className={
                  viewMode === "cowork"
                    ? "font-semibold text-ink border-b-2 border-ink pb-2"
                    : "text-ink-muted pb-2 hover:text-ink"
                }
              >
                Cowork
              </button>
            </div>

            {viewMode === "conversation" ? (
              <>
                <div className="px-3 pt-3">
                  <button
                    onClick={resetDemo}
                    className="w-full flex items-center gap-2 rounded-lg bg-surface px-3 py-2.5 text-sm font-medium text-ink hover:bg-hairline/40"
                  >
                    <IconEdit />
                    New conversation
                  </button>
                </div>

                <nav className="px-3 pt-2 text-sm">
                  {[
                    { icon: <IconSearch />, label: "Search" },
                    { icon: <IconLibrary />, label: "Library" },
                    { icon: <IconTasks />, label: "Tasks" },
                    { icon: <IconFolder />, label: "Notebooks" },
                    { icon: <IconAssistant />, label: "Assistants" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center gap-3 rounded-lg px-3 py-2 text-ink-muted hover:bg-surface cursor-default"
                    >
                      {item.icon}
                      {item.label}
                    </div>
                  ))}
                </nav>

                <div className="px-4 pt-4 text-xs font-semibold text-ink-muted">Pinned</div>
                <div className="px-3 pt-1 overflow-y-auto">
                  {pinnedAgents.map((agent) => (
                    <div
                      key={agent.name}
                      className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-surface cursor-default"
                    >
                      <span
                        className="w-6 h-6 rounded-md shrink-0"
                        style={{ background: agent.color }}
                        aria-hidden
                      />
                      <div className="min-w-0">
                        <p className="truncate font-medium text-ink">{agent.name}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="px-4 pt-4 text-xs font-semibold text-ink-muted">Conversations</div>
                <div className="px-3 pt-1 flex-1 overflow-y-auto">
                  {conversationHistory.map((title) => (
                    <div
                      key={title}
                      className="truncate rounded-lg px-3 py-2 text-sm text-ink-muted hover:bg-surface cursor-default"
                    >
                      {title}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <div className="px-3 pt-3">
                  <div className="w-full flex items-center gap-2 rounded-lg bg-ink px-3 py-2.5 text-sm font-medium text-white cursor-default">
                    <IconPlus />
                    New task
                  </div>
                </div>

                <nav className="px-3 pt-2 text-sm">
                  {[
                    { icon: <IconTasks />, label: "My tasks" },
                    { icon: <IconFolder />, label: "Scheduled" },
                    { icon: <IconAssistant />, label: "Customize" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center gap-3 rounded-lg px-3 py-2 text-ink-muted hover:bg-surface cursor-default"
                    >
                      {item.icon}
                      {item.label}
                    </div>
                  ))}
                </nav>

                <div className="px-4 pt-4 text-xs font-semibold text-ink-muted">Recent tasks</div>
                <div className="px-3 pt-1 flex-1 overflow-y-auto">
                  {coworkTaskOpen && (
                    <div className="truncate rounded-lg bg-surface px-3 py-2 text-sm font-medium text-ink">
                      Veloa Performance {"\u2014"} GTM Plan
                    </div>
                  )}
                  {coworkUpcomingTasks.map((task) => (
                    <div
                      key={task.title}
                      className="truncate rounded-lg px-3 py-2 text-sm text-ink-muted hover:bg-surface cursor-default"
                    >
                      {task.title}
                    </div>
                  ))}
                </div>
              </>
            )}

            <div className="border-t border-hairline px-4 py-3 flex items-center gap-3">
              <span className="w-8 h-8 rounded-full overflow-hidden shrink-0 bg-surface flex items-center justify-center">
                {!profile.user.photo ? (
                  <span className="text-xs font-semibold text-ink-muted">
                    {nameInitials(profile.user.firstName, profile.user.lastName)}
                  </span>
                ) : profile.user.photo.startsWith("data:") ? (
                  <img
                    src={profile.user.photo}
                    alt={userFullName}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src={profile.user.photo}
                    alt={userFullName}
                    width={32}
                    height={32}
                    className="w-full h-full object-cover"
                  />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-ink">{userFullName}</p>
                <p className="truncate text-xs text-ink-muted">M365 Copilot</p>
              </div>
              <IconMore />
            </div>
          </aside>

          {/* Main */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-between border-b border-hairline px-3 md:px-6 py-2.5 md:py-3">
              <div className="flex items-center gap-2 md:gap-4">
                <button
                  type="button"
                  onClick={() => setMobileSidebarOpen(true)}
                  className="md:hidden p-1.5 -ml-1 rounded-lg text-ink-muted hover:bg-surface"
                  aria-label="Open menu"
                >
                  <IconMenu />
                </button>
                {viewMode === "conversation" ? (
                  <>
                    <span className="hidden md:inline-block rounded-full bg-surface px-3 py-1.5 text-sm font-medium text-ink">Work IQ</span>
                    <span className="hidden md:flex items-center gap-1 text-sm text-ink-muted">
                      Automatic <IconChevronDown />
                    </span>
                  </>
                ) : (
                  <span className="hidden md:flex items-center gap-1 text-sm text-ink-muted">
                    Auto <IconChevronDown />
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 md:gap-4 text-ink-muted">
                <button
                  type="button"
                  onClick={() => {
                    setProfileDraft(profile);
                    setProfileError("");
                    setSettingsOpen(true);
                  }}
                  className="hover:text-ink transition-colors"
                  aria-label="Settings"
                  title="Settings"
                >
                  <IconSettings />
                </button>
                <IconShield />
                <IconChat />
                <span className="hidden md:inline-flex">
                  <IconMore />
                </span>
              </div>
            </div>

            {settingsOpen && (
              <div
                className="fixed inset-0 z-50 flex items-start justify-end bg-black/20 px-4 py-16 md:px-8"
                onClick={() => setSettingsOpen(false)}
              >
                <div
                  className="w-full max-w-sm max-h-[80vh] overflow-y-auto rounded-lg border border-[#E1DFDD] bg-white p-5 shadow-lg animate-fade-in-up"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold text-[#252423]">Settings</h2>
                    <button
                      type="button"
                      onClick={() => setSettingsOpen(false)}
                      className="text-[#605E5C] hover:text-[#252423]"
                      aria-label="Close"
                    >
                      <IconClose />
                    </button>
                  </div>

                  <p className="text-2xs font-semibold uppercase tracking-wide text-[#605E5C] mb-2">
                    Your profile
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-[#605E5C] mb-1.5">First name</label>
                      <input
                        type="text"
                        value={profileDraft.user.firstName}
                        onChange={(e) =>
                          setProfileDraft((prev) => ({
                            ...prev,
                            user: { ...prev.user, firstName: e.target.value },
                          }))
                        }
                        placeholder="First name"
                        className="w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[#605E5C] mb-1.5">Last name</label>
                      <input
                        type="text"
                        value={profileDraft.user.lastName}
                        onChange={(e) =>
                          setProfileDraft((prev) => ({
                            ...prev,
                            user: { ...prev.user, lastName: e.target.value },
                          }))
                        }
                        placeholder="Last name"
                        className="w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                      />
                    </div>
                  </div>

                  <label className="mt-3 block text-xs font-medium text-[#605E5C] mb-1.5">Photo</label>
                  <div className="flex items-center gap-3">
                    <span className="w-10 h-10 shrink-0 rounded-full overflow-hidden bg-[#F3F2F1] flex items-center justify-center text-xs font-semibold text-[#605E5C]">
                      {profileDraft.user.photo ? (
                        // Preview accepts both /public paths and uploaded data URLs.
                        <img
                          src={profileDraft.user.photo}
                          alt="Profile preview"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        nameInitials(profileDraft.user.firstName, profileDraft.user.lastName)
                      )}
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handlePhotoUpload(e.target.files?.[0])}
                      className="flex-1 text-2xs text-[#605E5C] file:mr-2 file:rounded-md file:border file:border-[#E1DFDD] file:bg-white file:px-2.5 file:py-1 file:text-2xs file:font-medium file:text-[#252423]"
                    />
                  </div>
                  <input
                    type="text"
                    value={profileDraft.user.photo.startsWith("data:") ? "" : profileDraft.user.photo}
                    onChange={(e) =>
                      setProfileDraft((prev) => ({
                        ...prev,
                        user: { ...prev.user, photo: e.target.value },
                      }))
                    }
                    placeholder=" or https://..."
                    className="mt-2 w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                  />
                  <p className="mt-1.5 text-2xs text-[#605E5C]">
                    Upload an image or paste a path/URL. Shown in the sidebar; the name is also used to sign
                    the emails CaldovaIQ sends on your behalf.
                  </p>

                  <div className="my-4 border-t border-[#E1DFDD]" />

                  <p className="text-2xs font-semibold uppercase tracking-wide text-[#605E5C] mb-2">
                    Approver
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-[#605E5C] mb-1.5">First name</label>
                      <input
                        type="text"
                        value={profileDraft.approver.firstName}
                        onChange={(e) =>
                          setProfileDraft((prev) => ({
                            ...prev,
                            approver: { ...prev.approver, firstName: e.target.value },
                          }))
                        }
                        placeholder="First name"
                        className="w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[#605E5C] mb-1.5">Last name</label>
                      <input
                        type="text"
                        value={profileDraft.approver.lastName}
                        onChange={(e) =>
                          setProfileDraft((prev) => ({
                            ...prev,
                            approver: { ...prev.approver, lastName: e.target.value },
                          }))
                        }
                        placeholder="Last name"
                        className="w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                      />
                    </div>
                  </div>

                  <label className="mt-3 block text-xs font-medium text-[#605E5C] mb-1.5">Job title</label>
                  <input
                    type="text"
                    value={profileDraft.approver.title}
                    onChange={(e) =>
                      setProfileDraft((prev) => ({
                        ...prev,
                        approver: { ...prev.approver, title: e.target.value },
                      }))
                    }
                    placeholder="National Commercial Director"
                    className="w-full rounded-md border border-[#E1DFDD] px-3 py-2 text-sm text-[#252423] outline-none focus:border-[#252423]"
                  />

                  {profileError && (
                    <p className="mt-2 text-2xs text-[#b3261e]">{profileError}</p>
                  )}

                  <div className="mt-4 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setSettingsOpen(false)}
                      className="rounded-md border border-[#E1DFDD] px-3.5 py-1.5 text-xs font-medium text-[#605E5C]"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={saveProfile}
                      className="rounded-md bg-[#252423] px-3.5 py-1.5 text-xs font-medium text-white hover:bg-[#252423]/85"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            )}

            {viewMode === "cowork" ? (
              !coworkTaskOpen ? (
              <div className="flex-1 overflow-y-auto px-5 md:px-6 py-8 md:py-10">
                <div className="max-w-3xl mx-auto">
                  <h1 className="text-2xl md:text-3xl font-medium text-ink mb-6 md:mb-8 text-left">
                    What can I do for you?
                  </h1>

                  <div className="w-full rounded-full border border-hairline flex items-center gap-3 px-4 md:px-5 py-3.5 md:py-4 text-ink-muted cursor-default">
                    <IconPlus />
                    <span className="flex-1 text-sm text-ink-muted">Start a task&hellip;</span>
                    <IconEdit />
                    <IconMic />
                  </div>

                  <div className="mt-8 flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-ink">Upcoming</h2>
                    <span className="text-sm text-ink-muted">Show more</span>
                  </div>
                  <div className="mt-3 rounded-2xl border border-hairline divide-y divide-hairline overflow-hidden">
                    {coworkUpcomingTasks.map((task) => (
                      <div
                        key={task.title}
                        onClick={task.action === "gtm" ? startCoworkTask : undefined}
                        className={`flex items-start gap-3 px-4 md:px-5 py-3.5 md:py-4 ${
                          task.action === "gtm" ? "cursor-pointer hover:bg-surface transition-colors" : ""
                        }`}
                      >
                        <span className="text-ink-muted mt-0.5 shrink-0">
                          <IconInfo />
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-ink">{task.title}</p>
                          <p className="text-xs text-ink-muted mt-0.5">{task.subtitle}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-ink">Try these</h2>
                    <span className="text-sm text-ink-muted">Show more</span>
                  </div>
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {coworkTryThese.map((item) => (
                      <div
                        key={item.label}
                        className="rounded-xl border border-hairline bg-white px-4 py-6 flex flex-col gap-4 cursor-default"
                      >
                        <span
                          className="w-9 h-9 rounded-lg shrink-0"
                          style={{ background: item.color }}
                          aria-hidden
                        />
                        <p className="text-sm font-medium text-ink">{item.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              ) : (
                <CoworkTaskView
                  events={veloaEvents}
                  eventIdx={coworkEventIdx}
                  status={coworkStatus}
                  taskStatus={coworkTaskStatus}
                  tasks={veloaTasks}
                  skillsUsed={veloaSkillsUsed}
                  onClose={closeCoworkTask}
                />
              )
            ) : !started ? (
              <div className="flex-1 flex flex-col items-center justify-center px-5 md:px-6">
                <h1 className="text-2xl md:text-3xl font-medium text-ink mb-6 md:mb-8 text-left md:text-center self-stretch md:self-auto">
                  What can I do for you?
                </h1>

                <button
                  type="button"
                  onClick={() => {
                    setActiveTrack(primaryTrackId);
                    startTyping(scenes[0].choices[0]);
                  }}
                  disabled={isBusy}
                  className="w-full max-w-2xl rounded-full border border-hairline flex items-center gap-3 px-4 md:px-5 py-3.5 md:py-4 text-ink-muted text-left hover:border-ink/40 transition-colors"
                >
                  <IconPlus />
                  <span className="flex-1 text-sm text-ink">
                    {draftText || "Message Copilot"}
                    {isTyping && <span className="inline-block w-px h-4 align-middle bg-ink ml-0.5 animate-pulse" />}
                  </span>
                  <IconMic />
                  <span className="w-8 h-8 rounded-full bg-surface flex items-center justify-center shrink-0">
                    <IconWave />
                  </span>
                </button>

                <div className="mt-3 flex flex-row flex-wrap items-center justify-center gap-1.5 w-full max-w-2xl">
                  {suggestedChips.map((chip) => {
                    // A chip that repeats the opening prompt starts the scenario on click.
                    const opener = scenes[0].choices[0];
                    const startsScenario =
                      chip === opener.user || chip === opener.label || chip === scenario.shell.openerChip;
                    if (chip === "Suggested") {
                      return (
                        <span key={chip} className="text-2xs uppercase tracking-wide text-ink-muted mr-1">
                          {chip}
                        </span>
                      );
                    }
                    if (!startsScenario) {
                      return (
                        <span
                          key={chip}
                          className="rounded-full border border-hairline px-3 py-1 text-xs text-ink-muted whitespace-nowrap"
                        >
                          {chip}
                        </span>
                      );
                    }
                    return (
                      <button
                        key={chip}
                        type="button"
                        onClick={() => {
                          setActiveTrack(primaryTrackId);
                          startTyping(opener);
                        }}
                        disabled={isBusy}
                        title={opener.user}
                        className="flex items-center gap-1.5 rounded-full border border-[#6f5bd6]/40 bg-[#6f5bd6]/5 px-3 py-1 text-xs font-medium text-ink whitespace-nowrap hover:bg-[#6f5bd6]/10 hover:border-[#6f5bd6] transition-colors disabled:opacity-60"
                      >
                        <span className="text-[#6f5bd6] shrink-0 [&_svg]:w-3 [&_svg]:h-3">
                          <IconSparkle />
                        </span>
                        {chip}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              <>
                <div ref={conversationRef} className="flex-1 overflow-y-auto px-3 md:px-6 py-4 md:py-6 space-y-4">
                  {messages.map((msg, i) => {
                    const identity = msg.role === "assistant" ? getIdentity(msg.mention) : null;
                    return (
                      <div
                        key={`${msg.role}-${i}`}
                        className={`rounded-2xl border border-hairline px-3 md:px-4 py-3 text-sm ${
                          msg.role === "user" ? "ml-auto max-w-[85%] md:max-w-[70%] bg-surface" : "max-w-[95%] md:max-w-[85%] bg-white"
                        } ${msg.scenarios ? "w-full max-w-[95%] md:max-w-[820px]" : ""}`}
                      >
                        {identity && (
                          <div className="mb-2 flex items-center gap-2">
                            <AgentAvatar name={identity.name} color={identity.color} icon={identity.icon} />
                            <span className="text-sm font-semibold text-ink">{identity.name}</span>
                          </div>
                        )}

                        {msg.mention && msg.role === "user" && (
                          <span className="mr-1 inline-block rounded-md bg-[#0f7a6c]/10 px-1.5 py-0.5 text-xs font-medium text-[#0f7a6c]">
                            @{msg.mention}
                          </span>
                        )}

                        {msg.report ? (
                          <ReportView report={msg.report} />
                        ) : msg.role === "assistant" ? (
                          renderMarkdown(msg.text)
                        ) : (
                          <span className="whitespace-pre-line">{msg.text}</span>
                        )}

                        {msg.chart && <ReportChartCard chart={msg.chart} />}

                        {msg.reflection && (
                          <div className="mt-3 border-t border-hairline pt-3">{renderMarkdown(msg.reflection)}</div>
                        )}

                        {msg.person && <PersonCard person={msg.person} />}

                        {msg.emailDraft && (
                          <EmailDraftCard
                            draft={msg.emailDraft}
                            sent={emailSent}
                            sending={emailSending}
                            onSend={sendEmailAndNotify}
                            onSelectSource={setSelectedSource}
                          />
                        )}

                        {msg.scenarios && (
                          <ScenarioCarousel
                            scenarios={msg.scenarios}
                            selectedId={selectedScenarioId}
                            disabled={isBusy}
                            onSelect={handleScenarioSelect}
                          />
                        )}

                        {msg.role === "assistant" && !msg.report && (
                          <>
                            {msg.chain && (
                              <p className="mt-3 text-2xs text-ink-muted/80">Source: {msg.chain}</p>
                            )}
                            <MessageActionBar text={msg.text} />
                          </>
                        )}

                        <SourceChips sources={msg.sources} onSelect={setSelectedSource} />
                      </div>
                    );
                  })}

                  {processingStep && (
                    <div className="max-w-[85%] rounded-2xl border border-hairline bg-white px-4 py-3 text-sm">
                      {pendingChoice && (
                        <div className="mb-2 flex items-center gap-2">
                          <AgentAvatar
                            name={getIdentity(pendingChoice.mention).name}
                            color={getIdentity(pendingChoice.mention).color}
                            icon={getIdentity(pendingChoice.mention).icon}
                          />
                          <span className="text-sm font-semibold text-ink">{getIdentity(pendingChoice.mention).name}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 font-medium text-ink">
                        <span className="text-[#0f7a6c] animate-pulse">
                          <IconSparkle />
                        </span>
                        {processingStep.label}
                        <span className="inline-flex gap-0.5 ml-1">
                          <span className="w-1 h-1 rounded-full bg-ink-muted animate-bounce [animation-delay:-0.2s]" />
                          <span className="w-1 h-1 rounded-full bg-ink-muted animate-bounce [animation-delay:-0.1s]" />
                          <span className="w-1 h-1 rounded-full bg-ink-muted animate-bounce" />
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-ink-muted">{processingStep.sub}</p>
                    </div>
                  )}

                  {isAssistantTyping && (
                    <div className="max-w-[85%] rounded-2xl border border-hairline bg-white px-4 py-3 text-sm">
                      {pendingChoice && (
                        <div className="mb-2 flex items-center gap-2">
                          <AgentAvatar
                            name={getIdentity(pendingChoice.mention).name}
                            color={getIdentity(pendingChoice.mention).color}
                            icon={getIdentity(pendingChoice.mention).icon}
                          />
                          <span className="text-sm font-semibold text-ink">{getIdentity(pendingChoice.mention).name}</span>
                        </div>
                      )}
                      <span className="whitespace-pre-line">{assistantDraft}</span>
                      <span className="inline-block w-px h-4 align-middle bg-ink ml-0.5 animate-pulse" />
                    </div>
                  )}

                  {isFinished && !isBusy && (
                    <div className="flex justify-center pt-2">
                      <button
                        type="button"
                        onClick={resetDemo}
                        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs text-ink-muted hover:bg-hairline/40 hover:text-ink"
                      >
                        <IconEdit />
                        New conversation
                      </button>
                    </div>
                  )}
                </div>

                <div className="relative border-t border-hairline px-3 md:px-6 py-3 md:py-4">
                  {mentionMenuOpen && (
                    <div className="absolute bottom-full left-3 md:left-6 right-3 md:right-auto mb-2 w-auto md:w-80 rounded-xl border border-hairline bg-white shadow-xl p-2 z-10">
                      <p className="px-2 pb-1 text-xs font-semibold text-ink-muted">Agents</p>
                      {mentionHint && (
                        <p className="mx-2 mb-2 rounded-md bg-surface px-2 py-1.5 text-xs text-ink">
                          You pick one agent — it routes the question for you:
                          <span className="block font-medium">{mentionHint}</span>
                          <span className="block mt-1 text-ink-muted">Take your time — click Continue when ready.</span>
                        </p>
                      )}
                      {pinnedAgents.map((agent, idx) => (
                        <div
                          key={agent.name}
                          className={`flex items-center gap-3 rounded-lg px-2 py-2 text-sm ${
                            idx === 0 ? "border border-ink/70 bg-surface" : ""
                          }`}
                        >
                          <span className="w-7 h-7 rounded-md shrink-0" style={{ background: agent.color }} aria-hidden />
                          <div className="min-w-0 flex-1">
                            <p className="truncate font-medium text-ink">{agent.name}</p>
                            <p className="truncate text-xs text-ink-muted">{agent.sub}</p>
                          </div>
                          {idx === 0 && mentionTarget && (
                            <span className="shrink-0 rounded-md bg-ink px-1.5 py-0.5 text-2xs font-medium text-white">
                              @{mentionTarget}
                            </span>
                          )}
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={continueMention}
                        className="mt-2 w-full rounded-lg bg-ink px-3 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity"
                      >
                        Continue with @{mentionTarget ?? pinnedAgents[0]?.name ?? "agent"} →
                      </button>
                    </div>
                  )}

                  {!isFinished && !isBusy && visibleChoices.length > 0 && (
                    <div className="mb-2 flex flex-wrap items-start justify-end gap-2">
                      {visibleChoices.map((choice) => (
                        <button
                          key={choice.label}
                          type="button"
                          onClick={() => (choice.opensModal ? viewApprovalPolicy() : startTyping(choice))}
                          className="rounded-lg border border-hairline bg-white px-4 py-2 text-left text-sm hover:bg-surface hover:border-ink/40 transition-colors"
                        >
                          {choice.label}
                        </button>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => !isFinished && visibleChoices[0] && startTyping(visibleChoices[0])}
                    disabled={isBusy || isFinished || visibleChoices.length === 0}
                    className="w-full rounded-full border border-hairline flex items-center gap-3 px-5 py-3 text-left text-ink-muted hover:border-ink/40 transition-colors disabled:hover:border-hairline"
                  >
                    <IconPlus />
                    <span className="flex-1 text-sm text-ink">
                      {draftText
                        ? renderDraftWithMention(draftText)
                        : isFinished
                          ? "Message"
                          : visibleChoices.length === 0
                            ? "Waiting for your selection above \u2014 pick a scenario to continue"
                            : isBusy
                              ? "Copilot is working \u2014 please wait"
                              : "Click here, or pick a suggested reply above, to type the next message"}
                      {isTyping && (
                        <span className="inline-block w-px h-4 align-middle bg-ink ml-0.5 animate-pulse" />
                      )}
                    </span>
                    <IconMic />
                  </button>
                </div>
              </>
            )}
          </div>

          {selectedSource && <SourcePanel source={selectedSource} onClose={() => setSelectedSource(null)} />}
          {approvalPolicyOpen && approverAuthorizationStatus && (
            <ApprovalPolicyModal
              authorization={resolveTokens(approverAuthorizationStatus, tokens)}
              onClose={closeApprovalPolicy}
            />
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- Structured mailbox-style report view ---------- */








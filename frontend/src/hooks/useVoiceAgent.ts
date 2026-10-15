import { useCallback, useRef, useState } from "react";
import type { AgentStatus, CallSummaryData, ChatMessage } from "../types/voice";
import { sendChatMessage } from "../services/chatApi";
import { cleanSpeechText } from "../utils/speechText";
import { normalizeOrderReferences } from "../utils/orderId";
import { createCallSummary } from "../utils/summary";

export type ConversationLanguage = "english" | "hinglish";
export type VoicePreference = "auto" | "indian-hindi";

type VoiceAgentOptions = {
  language: ConversationLanguage;
  voicePreference: VoicePreference;
};

type RecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type RecognitionConstructor = new () => RecognitionInstance;

const INACTIVITY_TIMEOUT_MS = 15_000;

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function recognitionLocale(_language: ConversationLanguage): string {
  // English is used for both modes because browser speech recognition does not
  // provide a reliable dedicated Hinglish locale.
  return "en-IN";
}

function speechLocale(
  language: ConversationLanguage,
  preference: VoicePreference,
): string {
  if (preference === "indian-hindi") return "hi-IN";
  // Automatic mode still prefers Hindi for Hinglish and Indian English for English.
  return language === "hinglish" ? "hi-IN" : "en-IN";
}

function isLikelyFemaleVoice(voice: SpeechSynthesisVoice): boolean {
  // Browsers do not expose a standard gender property. Use common voice-name
  // hints where available, then fall back to a matching-language voice.
  return /female|woman|swara|heera|kalpana|priya|neelam|aarti|lekha|raveena|samantha|zira|aria/i.test(
    voice.name,
  );
}

function chooseVoice(
  voices: SpeechSynthesisVoice[],
  targetLocale: string,
): SpeechSynthesisVoice | undefined {
  const target = targetLocale.toLowerCase();
  const languageCode = target.split("-")[0];
  const exact = voices.filter((voice) => voice.lang.toLowerCase() === target);
  const sameLanguage = voices.filter(
    (voice) =>
      voice.lang.toLowerCase().startsWith(`${languageCode}-`) ||
      voice.lang.toLowerCase() === languageCode,
  );
  const femaleExact = exact.find(isLikelyFemaleVoice);
  if (femaleExact) return femaleExact;

  const femaleSameLanguage = sameLanguage.find(isLikelyFemaleVoice);
  if (femaleSameLanguage) return femaleSameLanguage;

  // Prefer a likely female voice even if the browser has no identifiable female
  // Hindi voice. Gender is not exposed consistently by the Web Speech API.
  const femaleIndianEnglish = voices.find(
    (voice) =>
      voice.lang.toLowerCase() === "en-in" && isLikelyFemaleVoice(voice),
  );
  if (femaleIndianEnglish) return femaleIndianEnglish;

  return (
    exact[0] ??
    sameLanguage[0] ??
    voices.find((voice) => voice.lang.toLowerCase() === "en-in")
  );
}

export function useVoiceAgent({
  language,
  voicePreference,
}: VoiceAgentOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AgentStatus>("Ready");
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<CallSummaryData | null>(null);
  const [isActive, setIsActive] = useState(false);

  const messagesRef = useRef<ChatMessage[]>([]);
  const recognitionRef = useRef<RecognitionInstance | null>(null);
  const activeRef = useRef(false);
  const busyRef = useRef(false);
  const speakingRef = useRef(false);
  const recognitionStartingRef = useRef(false);
  const sessionIdRef = useRef(0);
  const speechTokenRef = useRef(0);
  const lastInterimRef = useRef("");
  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastActivityAtRef = useRef(Date.now());

  const clearInactivityTimer = useCallback(() => {
    if (inactivityTimerRef.current !== null) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
  }, []);

  const addMessage = useCallback(
    (speaker: ChatMessage["speaker"], text: string) => {
      const message: ChatMessage = {
        id: createId(),
        speaker,
        text,
        timestamp: new Date().toISOString(),
      };
      const nextMessages = [...messagesRef.current, message];
      messagesRef.current = nextMessages;
      setMessages(nextMessages);
    },
    [],
  );

  const stopRecognition = useCallback(() => {
    recognitionStartingRef.current = false;
    clearInactivityTimer();
    try {
      recognitionRef.current?.abort();
    } catch {
      // Recognition may already have stopped.
    }
  }, [clearInactivityTimer]);

  const stopSpeech = useCallback(() => {
    speechTokenRef.current += 1;
    speakingRef.current = false;
    try {
      window.speechSynthesis?.cancel();
    } catch {
      // Speech may already have stopped.
    }
  }, []);

  const scheduleInactivityTimeout = useCallback(
    (sessionId: number) => {
      clearInactivityTimer();
      if (!activeRef.current || busyRef.current || speakingRef.current) return;

      const elapsed = Date.now() - lastActivityAtRef.current;
      const remaining = Math.max(0, INACTIVITY_TIMEOUT_MS - elapsed);

      inactivityTimerRef.current = setTimeout(() => {
        inactivityTimerRef.current = null;
        if (!activeRef.current || sessionId !== sessionIdRef.current) return;
        if (busyRef.current || speakingRef.current) return;

        activeRef.current = false;
        busyRef.current = false;
        speakingRef.current = false;
        sessionIdRef.current += 1;
        stopRecognition();
        stopSpeech();

        setIsActive(false);
        setStatus("Call ended");
        setSummary(createCallSummary(messagesRef.current));
        setError(
          "Call paused due to inactivity. Click Start Call to resume or New Conversation to start over.",
        );
      }, remaining);
    },
    [clearInactivityTimer, stopRecognition, stopSpeech],
  );

  const restartRecognition = useCallback(() => {
    if (
      !activeRef.current ||
      recognitionStartingRef.current ||
      !recognitionRef.current
    ) {
      return;
    }
    try {
      recognitionStartingRef.current = true;
      recognitionRef.current.start();
      setStatus(speakingRef.current ? "Speaking" : "Listening");
      scheduleInactivityTimeout(sessionIdRef.current);
    } catch {
      recognitionStartingRef.current = false;
      // The browser may still be finalizing the previous recognition session.
    }
  }, [scheduleInactivityTimeout]);

  const speakReply = useCallback(
    (text: string, sessionId: number) => {
      const speechText = cleanSpeechText(text);

      if (!("speechSynthesis" in window)) {
        speakingRef.current = false;
        busyRef.current = false;
        if (activeRef.current) {
          lastActivityAtRef.current = Date.now();
          setError(
            "Voice playback is unavailable. You can continue by speaking.",
          );
          setStatus("Listening");
          restartRecognition();
          scheduleInactivityTimeout(sessionId);
        } else {
          setStatus("Call ended");
        }
        return;
      }

      stopSpeech();
      const speechToken = speechTokenRef.current;
      const utterance = new SpeechSynthesisUtterance(speechText);
      const targetLocale = speechLocale(language, voicePreference);
      utterance.lang = targetLocale;
      utterance.rate = 1.02;
      utterance.pitch = 1;

      const voices = window.speechSynthesis.getVoices();
      const voice = chooseVoice(voices, targetLocale);
      if (voice) utterance.voice = voice;

      utterance.onstart = () => {
        if (
          sessionId !== sessionIdRef.current ||
          speechToken !== speechTokenRef.current
        )
          return;
        speakingRef.current = true;
        setStatus("Speaking");
        restartRecognition();
      };

      utterance.onend = () => {
        if (
          sessionId !== sessionIdRef.current ||
          speechToken !== speechTokenRef.current
        )
          return;
        speakingRef.current = false;
        busyRef.current = false;
        if (activeRef.current) {
          lastActivityAtRef.current = Date.now();
          setStatus("Listening");
          restartRecognition();
          scheduleInactivityTimeout(sessionId);
        } else {
          setStatus("Call ended");
        }
      };

      utterance.onerror = (event) => {
        if (
          sessionId !== sessionIdRef.current ||
          speechToken !== speechTokenRef.current
        )
          return;
        if (event.error === "canceled" || event.error === "interrupted") return;
        speakingRef.current = false;
        busyRef.current = false;
        if (activeRef.current) {
          lastActivityAtRef.current = Date.now();
          setError(
            "I couldn't play the voice response. You can continue by speaking.",
          );
          setStatus("Listening");
          restartRecognition();
          scheduleInactivityTimeout(sessionId);
        } else {
          setStatus("Call ended");
        }
      };

      window.speechSynthesis.speak(utterance);
    },
    [
      language,
      restartRecognition,
      scheduleInactivityTimeout,
      stopSpeech,
      voicePreference,
    ],
  );

  const processMessage = useCallback(
    async (recognizedText: string, sessionId: number) => {
      if (busyRef.current || sessionId !== sessionIdRef.current) return;

      const message = normalizeOrderReferences(recognizedText).trim();
      if (!message) {
        setError("I couldn't understand that. Please try speaking again.");
        return;
      }

      clearInactivityTimer();
      busyRef.current = true;
      lastActivityAtRef.current = Date.now();
      setError("");
      setStatus("Thinking");

      const history = messagesRef.current.map((item) => ({
        role:
          item.speaker === "Customer"
            ? ("user" as const)
            : ("assistant" as const),
        content: item.text,
      }));

      addMessage("Customer", message);

      try {
        const result = await sendChatMessage(message, language, history);

        if (sessionId !== sessionIdRef.current || !activeRef.current) return;
        const reply = cleanSpeechText(result.reply);
        addMessage("Aria", reply);
        speakReply(reply, sessionId);
      } catch (caught) {
        if (sessionId !== sessionIdRef.current || !activeRef.current) return;
        const errorMessage =
          caught instanceof Error
            ? caught.message
            : "The support service is temporarily unavailable.";
        setError(errorMessage);
        busyRef.current = false;
        const fallback =
          language === "hinglish"
            ? "Sorry, main abhi aapki request process nahi kar paayi. Please dobara try karein."
            : "I'm sorry, I couldn't process that request just now. Please try asking again.";
        addMessage("Aria", fallback);
        speakReply(fallback, sessionId);
      }
    },
    [addMessage, clearInactivityTimer, language, speakReply],
  );

  const startCall = useCallback(() => {
    if (activeRef.current) return;
    setError("");
    setSummary(null);

    const browserWindow = window as typeof window & {
      SpeechRecognition?: RecognitionConstructor;
      webkitSpeechRecognition?: RecognitionConstructor;
    };
    const SpeechRecognition =
      browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        "Speech recognition is unavailable in this browser. Please try Chrome and allow microphone access.",
      );
      return;
    }

    stopRecognition();
    stopSpeech();
    const recognition = new SpeechRecognition();
    const sessionId = ++sessionIdRef.current;

    recognition.lang = recognitionLocale(language);
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: any) => {
      if (!activeRef.current || sessionId !== sessionIdRef.current) return;
      let finalText = "";
      let interimText = "";

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const transcript = String(result?.[0]?.transcript || "").trim();
        if (result.isFinal) finalText += `${transcript} `;
        else interimText += `${transcript} `;
      }

      const interim = interimText.trim();
      if (interim) {
        lastActivityAtRef.current = Date.now();
        clearInactivityTimer();
      }

      if (
        speakingRef.current &&
        interim &&
        interim !== lastInterimRef.current
      ) {
        lastInterimRef.current = interim;
        stopSpeech();
        busyRef.current = false;
        setStatus("Listening");
      }

      if (finalText.trim()) {
        clearInactivityTimer();
        lastInterimRef.current = "";
        if (speakingRef.current) {
          stopSpeech();
          busyRef.current = false;
        }
        lastActivityAtRef.current = Date.now();
        void processMessage(finalText.trim(), sessionId);
        return;
      }

      if (interim && !busyRef.current && !speakingRef.current) {
        scheduleInactivityTimeout(sessionId);
      }
    };

    recognition.onerror = (event: any) => {
      recognitionStartingRef.current = false;
      if (!activeRef.current || sessionId !== sessionIdRef.current) return;

      if (
        event.error === "not-allowed" ||
        event.error === "service-not-allowed"
      ) {
        setError(
          "Microphone access was denied. Allow microphone access in your browser settings.",
        );
        activeRef.current = false;
        busyRef.current = false;
        speakingRef.current = false;
        stopRecognition();
        stopSpeech();
        setIsActive(false);
        setStatus("Error");
      } else if (event.error !== "no-speech" && event.error !== "aborted") {
        setError(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      recognitionStartingRef.current = false;
      if (activeRef.current && sessionId === sessionIdRef.current)
        restartRecognition();
    };

    recognitionRef.current = recognition;
    activeRef.current = true;
    busyRef.current = false;
    speakingRef.current = false;
    lastInterimRef.current = "";
    lastActivityAtRef.current = Date.now();
    setIsActive(true);
    setStatus("Listening");

    try {
      recognitionStartingRef.current = true;
      recognition.start();
      scheduleInactivityTimeout(sessionId);
    } catch {
      recognitionStartingRef.current = false;
      activeRef.current = false;
      stopRecognition();
      setIsActive(false);
      setStatus("Ready");
      setError("Couldn't start speech recognition. Please try again.");
    }
  }, [
    clearInactivityTimer,
    language,
    processMessage,
    restartRecognition,
    scheduleInactivityTimeout,
    stopRecognition,
    stopSpeech,
  ]);

  const endCall = useCallback(() => {
    activeRef.current = false;
    busyRef.current = false;
    speakingRef.current = false;
    sessionIdRef.current += 1;
    stopRecognition();
    stopSpeech();
    setIsActive(false);
    setStatus("Call ended");
    setSummary(createCallSummary(messagesRef.current));
    setError("");
  }, [stopRecognition, stopSpeech]);

  const resetCall = useCallback(() => {
    activeRef.current = false;
    busyRef.current = false;
    speakingRef.current = false;
    sessionIdRef.current += 1;
    stopRecognition();
    stopSpeech();
    messagesRef.current = [];
    setMessages([]);
    setSummary(null);
    setError("");
    setIsActive(false);
    setStatus("Ready");
  }, [stopRecognition, stopSpeech]);

  return {
    messages,
    status,
    error,
    summary,
    isActive,
    startCall,
    endCall,
    resetCall,
  };
}

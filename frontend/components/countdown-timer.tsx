"use client";

import { useState, useEffect } from "react";
import { Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface CountdownTimerProps {
  targetTime: string;
  onExpire?: () => void;
  label?: string;
}

export function CountdownTimer({ targetTime, onExpire, label = "Time Remaining" }: CountdownTimerProps) {
  const [timeLeft, setTimeLeft] = useState<{
    minutes: number;
    seconds: number;
    isExpired: boolean;
    isLate: boolean;
  }>({ minutes: 0, seconds: 0, isExpired: false, isLate: false });

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date().getTime();
      const target = new Date(targetTime).getTime();
      const difference = target - now;

      if (difference <= 0) {
        const lateMinutes = Math.abs(Math.floor(difference / 1000 / 60));
        const lateSeconds = Math.abs(Math.floor((difference / 1000) % 60));
        return {
          minutes: lateMinutes,
          seconds: lateSeconds,
          isExpired: true,
          isLate: true,
        };
      }

      return {
        minutes: Math.floor((difference / 1000 / 60) % 60),
        seconds: Math.floor((difference / 1000) % 60),
        isExpired: false,
        isLate: false,
      };
    };

    const timer = setInterval(() => {
      const newTimeLeft = calculateTimeLeft();
      setTimeLeft(newTimeLeft);

      if (newTimeLeft.isExpired && !timeLeft.isExpired) {
        onExpire?.();
      }
    }, 1000);

    setTimeLeft(calculateTimeLeft());

    return () => clearInterval(timer);
  }, [targetTime, onExpire, timeLeft.isExpired]);

  const formatTime = (value: number) => value.toString().padStart(2, "0");

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg px-4 py-3",
        timeLeft.isLate
          ? "bg-destructive/10"
          : timeLeft.minutes < 5
          ? "bg-warning/10"
          : "bg-primary/10"
      )}
    >
      {timeLeft.isLate ? (
        <AlertTriangle className="h-5 w-5 text-destructive" />
      ) : (
        <Clock
          className={cn(
            "h-5 w-5",
            timeLeft.minutes < 5 ? "text-warning" : "text-primary"
          )}
        />
      )}
      <div>
        <p className="text-xs text-muted-foreground">
          {timeLeft.isLate ? "Late by" : label}
        </p>
        <p
          className={cn(
            "text-lg font-bold tabular-nums",
            timeLeft.isLate
              ? "text-destructive"
              : timeLeft.minutes < 5
              ? "text-warning"
              : "text-primary"
          )}
        >
          {formatTime(timeLeft.minutes)}:{formatTime(timeLeft.seconds)}
        </p>
      </div>
      {timeLeft.isLate && (
        <div className="ml-auto">
          <p className="text-xs text-muted-foreground">Penalty</p>
          <p className="text-sm font-medium text-destructive">
            ${((timeLeft.minutes * 60 + timeLeft.seconds) * 0.5 / 60).toFixed(2)}
          </p>
        </div>
      )}
    </div>
  );
}

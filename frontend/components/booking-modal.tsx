"use client";

import { useState } from "react";
import { X, Zap, AlertCircle, CheckCircle, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import type { ChargingSlot, BookingRequest } from "@/lib/api";

interface BookingModalProps {
  slot: ChargingSlot;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (booking: BookingRequest) => Promise<void>;
}

export function BookingModal({ slot, isOpen, onClose, onConfirm }: BookingModalProps) {
  const [formData, setFormData] = useState({
    driverId: "",
    startTime: "",
    endTime: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await onConfirm({
        driverId: formData.driverId,
        chargerId: slot.id,
        slotId: slot.id,
        startTime: formData.startTime,
        endTime: formData.endTime,
        deposit: slot.deposit,
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create booking");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleClose = () => {
    setFormData({ driverId: "", startTime: "", endTime: "" });
    setError(null);
    setSuccess(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl">
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>

        {success ? (
          <div className="flex flex-col items-center py-8 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/20">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-foreground">Booking Confirmed!</h2>
            <p className="mb-4 text-muted-foreground">
              Your charging slot has been reserved successfully.
            </p>
            <div className="mb-6 flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2">
              <Send className="h-4 w-4 text-primary" />
              <span className="text-sm text-foreground">Confirmation sent via Telegram</span>
            </div>
            <Button onClick={handleClose}>Close</Button>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/20">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-foreground">Book Charging Slot</h2>
                <p className="text-sm text-muted-foreground">Slot {slot.id} - {slot.type} Charger</p>
              </div>
            </div>

            {error && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="driverId" className="text-foreground">Driver ID</Label>
                <Input
                  id="driverId"
                  placeholder="Enter your driver ID"
                  value={formData.driverId}
                  onChange={(e) => handleChange("driverId", e.target.value)}
                  className="bg-secondary border-border"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="startTime" className="text-foreground">Start Time</Label>
                  <Input
                    id="startTime"
                    type="datetime-local"
                    value={formData.startTime}
                    onChange={(e) => handleChange("startTime", e.target.value)}
                    className="bg-secondary border-border"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="endTime" className="text-foreground">End Time</Label>
                  <Input
                    id="endTime"
                    type="datetime-local"
                    value={formData.endTime}
                    onChange={(e) => handleChange("endTime", e.target.value)}
                    className="bg-secondary border-border"
                    required
                  />
                </div>
              </div>

              <div className="rounded-lg bg-secondary/50 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Location</span>
                  <span className="text-sm font-medium text-foreground">{slot.location}</span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Price</span>
                  <span className="text-sm font-medium text-foreground">${slot.pricePerKwh}/kWh</span>
                </div>
                <div className="mt-2 flex items-center justify-between border-t border-border pt-2">
                  <span className="text-sm font-medium text-foreground">Deposit Required</span>
                  <span className="text-lg font-bold text-primary">${slot.deposit}</span>
                </div>
              </div>

              <div className="flex gap-3">
                <Button 
                  type="button" 
                  variant="outline" 
                  className="flex-1"
                  onClick={handleClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="flex-1 gap-2"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4" />
                      Confirm Booking
                    </>
                  )}
                </Button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

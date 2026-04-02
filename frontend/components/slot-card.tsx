"use client";

import { Zap, Battery, MapPin, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChargingSlot } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

interface SlotCardProps {
  slot: ChargingSlot;
  onBook?: (slot: ChargingSlot) => void;
}

const statusConfig = {
  available: {
    label: "Available",
    className: "bg-success/20 text-success",
  },
  occupied: {
    label: "Occupied",
    className: "bg-muted text-muted-foreground",
  },
  faulty: {
    label: "Faulty",
    className: "bg-destructive/20 text-destructive",
  },
  maintenance: {
    label: "Maintenance",
    className: "bg-warning/20 text-warning",
  },
};

export function SlotCard({ slot, onBook }: SlotCardProps) {
  const status = statusConfig[slot.status];

  return (
    <Card className="group relative overflow-hidden border-border bg-card transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary to-accent opacity-0 transition-opacity group-hover:opacity-100" />
      
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0 pb-3">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            slot.type === "Fast" ? "bg-primary/20" : "bg-accent/20"
          )}>
            {slot.type === "Fast" ? (
              <Zap className="h-5 w-5 text-primary" />
            ) : (
              <Battery className="h-5 w-5 text-accent" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Slot {slot.id}</h3>
            <p className="text-sm text-muted-foreground">{slot.type} Charger</p>
          </div>
        </div>
        <span className={cn(
          "rounded-full px-2.5 py-1 text-xs font-medium",
          status.className
        )}>
          {status.label}
        </span>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <MapPin className="h-4 w-4" />
          <span>{slot.location}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Zap className="h-4 w-4" />
          <span>{slot.powerOutput}</span>
        </div>
        <div className="flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium text-foreground">${slot.pricePerKwh}/kWh</span>
          </div>
          <span className="text-xs text-muted-foreground">Deposit: ${slot.deposit}</span>
        </div>
      </CardContent>

      <CardFooter className="pt-0">
        <Button
          className="w-full"
          variant={slot.status === "available" ? "default" : "secondary"}
          disabled={slot.status !== "available"}
          onClick={() => onBook?.(slot)}
        >
          {slot.status === "available" ? "Book Now" : "Unavailable"}
        </Button>
      </CardFooter>
    </Card>
  );
}

"use client";

import { Zap, Battery, AlertTriangle, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { ChargingSlot } from "@/lib/api";

interface StatsCardsProps {
  slots: ChargingSlot[];
}

export function StatsCards({ slots }: StatsCardsProps) {
  const stats = {
    total: slots.length,
    available: slots.filter((s) => s.status === "available").length,
    occupied: slots.filter((s) => s.status === "occupied").length,
    faulty: slots.filter((s) => s.status === "faulty" || s.status === "maintenance").length,
  };

  const cards = [
    {
      label: "Total Stations",
      value: stats.total,
      icon: Zap,
      iconColor: "text-primary",
      bgColor: "bg-primary/10",
    },
    {
      label: "Available",
      value: stats.available,
      icon: CheckCircle,
      iconColor: "text-success",
      bgColor: "bg-success/10",
    },
    {
      label: "Occupied",
      value: stats.occupied,
      icon: Battery,
      iconColor: "text-accent",
      bgColor: "bg-accent/10",
    },
    {
      label: "Under Maintenance",
      value: stats.faulty,
      icon: AlertTriangle,
      iconColor: "text-warning",
      bgColor: "bg-warning/10",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label} className="border-border bg-card">
          <CardContent className="flex items-center gap-4 p-4">
            <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${card.bgColor}`}>
              <card.icon className={`h-6 w-6 ${card.iconColor}`} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{card.label}</p>
              <p className="text-2xl font-bold text-foreground">{card.value}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

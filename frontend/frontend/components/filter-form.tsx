"use client";

import { useState } from "react";
import { Search, MapPin, Clock, DollarSign, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";

interface FilterFormProps {
  locations: string[];
  onFilter: (filters: FilterValues) => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

export interface FilterValues {
  location: string;
  date: string;
  startTime: string;
  endTime: string;
  maxPrice: number;
}

export function FilterForm({ locations, onFilter, onRefresh, isLoading }: FilterFormProps) {
  const [filters, setFilters] = useState<FilterValues>({
    location: "",
    date: "",
    startTime: "",
    endTime: "",
    maxPrice: 100,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilter(filters);
  };

  const handleChange = (key: keyof FilterValues, value: string | number) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <Card className="border-border bg-card">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-2">
              <Label htmlFor="location" className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="h-4 w-4" />
                Location
              </Label>
              <Select
                value={filters.location}
                onValueChange={(value) => handleChange("location", value)}
              >
                <SelectTrigger id="location" className="bg-secondary border-border">
                  <SelectValue placeholder="All Locations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Locations</SelectItem>
                  {locations.map((loc) => (
                    <SelectItem key={loc} value={loc}>
                      {loc}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="date" className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                Date
              </Label>
              <Input
                id="date"
                type="date"
                value={filters.date}
                onChange={(e) => handleChange("date", e.target.value)}
                className="bg-secondary border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="startTime" className="text-muted-foreground">
                Start Time
              </Label>
              <Input
                id="startTime"
                type="time"
                value={filters.startTime}
                onChange={(e) => handleChange("startTime", e.target.value)}
                className="bg-secondary border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="endTime" className="text-muted-foreground">
                End Time
              </Label>
              <Input
                id="endTime"
                type="time"
                value={filters.endTime}
                onChange={(e) => handleChange("endTime", e.target.value)}
                className="bg-secondary border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxPrice" className="flex items-center gap-2 text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                Max Price: ${filters.maxPrice}
              </Label>
              <Input
                id="maxPrice"
                type="range"
                min="10"
                max="100"
                value={filters.maxPrice}
                onChange={(e) => handleChange("maxPrice", Number(e.target.value))}
                className="bg-secondary"
              />
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={onRefresh}
              disabled={isLoading}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button type="submit" className="gap-2" disabled={isLoading}>
              <Search className="h-4 w-4" />
              Search Slots
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

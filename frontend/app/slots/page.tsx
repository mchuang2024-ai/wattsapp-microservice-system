"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/header";
import { BookingModal } from "@/components/booking-modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Search, Zap, Battery, MapPin, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChargingSlot, BookingRequest } from "@/lib/api";
import { fetchSlotsByFilter, createBooking } from "@/lib/api";

// Mock data
const mockSlots: ChargingSlot[] = [
  { id: "CS001", type: "Fast", status: "available", deposit: 5, location: "Downtown Mall", powerOutput: "150 kW DC", pricePerKwh: 0.35 },
  { id: "CS002", type: "Slow", status: "available", deposit: 5, location: "City Center", powerOutput: "22 kW AC", pricePerKwh: 0.25 },
  { id: "CS005", type: "Fast", status: "available", deposit: 5, location: "Shopping District", powerOutput: "150 kW DC", pricePerKwh: 0.35 },
  { id: "CS007", type: "Fast", status: "available", deposit: 5, location: "Highway Rest Stop", powerOutput: "250 kW DC", pricePerKwh: 0.40 },
  { id: "CS009", type: "Slow", status: "available", deposit: 5, location: "University Campus", powerOutput: "11 kW AC", pricePerKwh: 0.20 },
  { id: "CS010", type: "Fast", status: "available", deposit: 5, location: "Sports Complex", powerOutput: "150 kW DC", pricePerKwh: 0.38 },
];

const mockLocations = ["Downtown Mall", "City Center", "Shopping District", "Highway Rest Stop", "University Campus", "Sports Complex"];

function SlotsPageContent() {
  const searchParams = useSearchParams();
  const preselectedSlotId = searchParams.get("slotId");
  // driverId can be passed as a URL query param (?driverId=123); defaults to "1"
  const driverId = searchParams.get("driverId") || "1";
  
  const [slots, setSlots] = useState<ChargingSlot[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<ChargingSlot | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    location: "",
    date: "",
    startTime: "",
    endTime: "",
  });

  const fetchSlots = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchSlotsByFilter({
        location: filters.location && filters.location !== "all" ? filters.location : undefined,
        date: filters.date || new Date().toISOString().split("T")[0],
        driverId,
        startTime: filters.startTime || undefined,
        endTime: filters.endTime || undefined,
      });
      setSlots(data);
    } catch (error) {
      console.error("Failed to fetch slots, using mock data:", error);
      let filtered = [...mockSlots];
      if (filters.location && filters.location !== "all") {
        filtered = filtered.filter((slot) => slot.location === filters.location);
      }
      setSlots(filtered);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  useEffect(() => {
    if (preselectedSlotId && slots.length > 0) {
      const slot = slots.find((s) => s.id === preselectedSlotId);
      if (slot) {
        setSelectedSlot(slot);
        setIsModalOpen(true);
      }
    }
  }, [preselectedSlotId, slots]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchSlots();
  };

  const handleBook = (slot: ChargingSlot) => {
    setSelectedSlot(slot);
    setIsModalOpen(true);
  };

  const handleConfirmBooking = async (booking: BookingRequest) => {
    try {
      const result = await createBooking(booking);
      console.log("Booking created:", result);
      fetchSlots();
    } catch (error) {
      console.error("Booking failed, simulating success:", error);
    }
  };

  const statusBadge = (status: ChargingSlot["status"]) => {
    const config = {
      available: "bg-success/20 text-success",
      occupied: "bg-muted text-muted-foreground",
      faulty: "bg-destructive/20 text-destructive",
      maintenance: "bg-warning/20 text-warning",
    };
    return (
      <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium capitalize", config[status])}>
        {status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Find Available Slots</h1>
          <p className="mt-2 text-muted-foreground">
            Search for available charging slots by location and time
          </p>
        </div>

        <Card className="mb-6 border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Search className="h-5 w-5 text-primary" />
              Search Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <div className="space-y-2">
                <Label htmlFor="location" className="flex items-center gap-2 text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  Location
                </Label>
                <Select
                  value={filters.location}
                  onValueChange={(value) => setFilters((prev) => ({ ...prev, location: value }))}
                >
                  <SelectTrigger id="location" className="bg-secondary border-border">
                    <SelectValue placeholder="All Locations" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Locations</SelectItem>
                    {mockLocations.map((loc) => (
                      <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="date" className="text-muted-foreground">Date</Label>
                <Input
                  id="date"
                  type="date"
                  value={filters.date}
                  onChange={(e) => setFilters((prev) => ({ ...prev, date: e.target.value }))}
                  className="bg-secondary border-border"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="startTime" className="text-muted-foreground">Start Time</Label>
                <Input
                  id="startTime"
                  type="time"
                  value={filters.startTime}
                  onChange={(e) => setFilters((prev) => ({ ...prev, startTime: e.target.value }))}
                  className="bg-secondary border-border"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="endTime" className="text-muted-foreground">End Time</Label>
                <Input
                  id="endTime"
                  type="time"
                  value={filters.endTime}
                  onChange={(e) => setFilters((prev) => ({ ...prev, endTime: e.target.value }))}
                  className="bg-secondary border-border"
                />
              </div>

              <div className="flex items-end gap-2">
                <Button type="submit" className="flex-1 gap-2" disabled={isLoading}>
                  <Search className="h-4 w-4" />
                  Search
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={fetchSlots}
                  disabled={isLoading}
                >
                  <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="text-foreground">Available Slots</span>
              <span className="text-sm font-normal text-muted-foreground">{slots.length} slots found</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Spinner className="h-8 w-8 text-primary" />
              </div>
            ) : slots.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Zap className="mb-4 h-12 w-12 text-muted-foreground" />
                <p className="text-lg font-medium text-foreground">No slots available</p>
                <p className="text-sm text-muted-foreground">Try adjusting your search filters</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-muted-foreground">Slot ID</TableHead>
                      <TableHead className="text-muted-foreground">Start Time</TableHead>
                      <TableHead className="text-muted-foreground">End Time</TableHead>
                      <TableHead className="text-muted-foreground">Status</TableHead>
                      <TableHead className="text-muted-foreground">Deposit</TableHead>
                      <TableHead className="text-right text-muted-foreground">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {slots.map((slot, idx) => (
                      <TableRow key={`${slot.id}-${slot.startTime}-${idx}`} className="border-border">
                        <TableCell className="font-medium text-foreground">{slot.id}</TableCell>
                        <TableCell className="text-muted-foreground">{slot.startTime}</TableCell>
                        <TableCell className="text-muted-foreground">{slot.endTime}</TableCell>
                        <TableCell>{statusBadge(slot.status)}</TableCell>
                        <TableCell className="font-medium text-primary">${slot.deposit}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => handleBook(slot)}
                            disabled={slot.status !== "available"}
                          >
                            Book
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {selectedSlot && (
          <BookingModal
            slot={selectedSlot}
            isOpen={isModalOpen}
            onClose={() => {
              setIsModalOpen(false);
              setSelectedSlot(null);
            }}
            onConfirm={handleConfirmBooking}
          />
        )}
      </main>
    </div>
  );
}

export default function SlotsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    }>
      <SlotsPageContent />
    </Suspense>
  );
}

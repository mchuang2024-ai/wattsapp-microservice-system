"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/header";
import { CountdownTimer } from "@/components/countdown-timer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Clock,
  Calendar,
  AlertTriangle,
  XCircle,
  CheckCircle,
  RefreshCw,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Booking } from "@/lib/api";

// Mock bookings data
const mockBookings: Booking[] = [
  {
    id: "BK001",
    driverId: "DR001",
    chargerId: "CS001",
    slotId: "CS001",
    startTime: new Date(Date.now() + 30 * 60000).toISOString(), // 30 mins from now
    endTime: new Date(Date.now() + 90 * 60000).toISOString(),
    status: "pending",
    deposit: 5,
    createdAt: new Date().toISOString(),
  },
  {
    id: "BK002",
    driverId: "DR001",
    chargerId: "CS002",
    slotId: "CS002",
    startTime: new Date(Date.now() - 10 * 60000).toISOString(), // 10 mins ago (late)
    endTime: new Date(Date.now() + 50 * 60000).toISOString(),
    status: "active",
    deposit: 5,
    createdAt: new Date(Date.now() - 60 * 60000).toISOString(),
    checkedInAt: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    id: "BK003",
    driverId: "DR001",
    chargerId: "CS005",
    slotId: "CS005",
    startTime: new Date(Date.now() - 120 * 60000).toISOString(),
    endTime: new Date(Date.now() - 60 * 60000).toISOString(),
    status: "completed",
    deposit: 5,
    createdAt: new Date(Date.now() - 180 * 60000).toISOString(),
  },
  {
    id: "BK004",
    driverId: "DR001",
    chargerId: "CS007",
    slotId: "CS007",
    startTime: new Date(Date.now() - 240 * 60000).toISOString(),
    endTime: new Date(Date.now() - 180 * 60000).toISOString(),
    status: "no-show",
    deposit: 5,
    createdAt: new Date(Date.now() - 300 * 60000).toISOString(),
    penalty: 15,
  },
];

const statusConfig = {
  pending: { label: "Pending", className: "bg-warning/20 text-warning", icon: Clock },
  active: { label: "Active", className: "bg-success/20 text-success", icon: Zap },
  completed: { label: "Completed", className: "bg-muted text-muted-foreground", icon: CheckCircle },
  cancelled: { label: "Cancelled", className: "bg-muted text-muted-foreground", icon: XCircle },
  "no-show": { label: "No Show", className: "bg-destructive/20 text-destructive", icon: AlertTriangle },
  late: { label: "Late", className: "bg-warning/20 text-warning", icon: AlertTriangle },
};

export default function BookingsPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [cancelDialog, setCancelDialog] = useState<{ open: boolean; bookingId: string | null }>({
    open: false,
    bookingId: null,
  });
  const [noShowDialog, setNoShowDialog] = useState<{ open: boolean; booking: Booking | null }>({
    open: false,
    booking: null,
  });

  const fetchBookings = useCallback(async () => {
    setIsLoading(true);
    try {
      // Replace with actual API call:
      // const data = await fetchBookings("DR001");
      // setBookings(data);
      
      await new Promise((resolve) => setTimeout(resolve, 500));
      setBookings(mockBookings);
    } catch (error) {
      console.error("Failed to fetch bookings:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const handleCheckInLate = async (booking: Booking) => {
    setNoShowDialog({ open: true, booking });
  };

  const confirmNoShow = async () => {
    if (!noShowDialog.booking) return;
    
    setActionLoading(noShowDialog.booking.id);
    try {
      // Replace with actual API call:
      // const result = await handleNoShow(noShowDialog.booking.id);
      
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Update local state
      setBookings((prev) =>
        prev.map((b) =>
          b.id === noShowDialog.booking?.id
            ? { ...b, status: "no-show" as const, penalty: 15 }
            : b
        )
      );
    } catch (error) {
      console.error("Failed to handle no-show:", error);
    } finally {
      setActionLoading(null);
      setNoShowDialog({ open: false, booking: null });
    }
  };

  const handleCancel = async (bookingId: string) => {
    setCancelDialog({ open: true, bookingId });
  };

  const confirmCancel = async () => {
    if (!cancelDialog.bookingId) return;
    
    setActionLoading(cancelDialog.bookingId);
    try {
      // Replace with actual API call:
      // await cancelBooking(cancelDialog.bookingId);
      
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setBookings((prev) =>
        prev.map((b) =>
          b.id === cancelDialog.bookingId
            ? { ...b, status: "cancelled" as const }
            : b
        )
      );
    } catch (error) {
      console.error("Failed to cancel booking:", error);
    } finally {
      setActionLoading(null);
      setCancelDialog({ open: false, bookingId: null });
    }
  };

  const handleReportFault = (booking: Booking) => {
    router.push(`/fault?bookingId=${booking.id}&slotId=${booking.slotId}&driverId=${booking.driverId}`);
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">My Bookings</h1>
            <p className="mt-2 text-muted-foreground">
              View and manage your charging slot reservations
            </p>
          </div>
          <Button
            variant="outline"
            onClick={fetchBookings}
            disabled={isLoading}
            className="gap-2"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            Refresh
          </Button>
        </div>

        {/* Active Booking Timer */}
        {bookings
          .filter((b) => b.status === "pending" || b.status === "active")
          .map((booking) => (
            <Card key={booking.id} className="mb-6 border-primary/50 bg-card">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg text-foreground">
                  <Zap className="h-5 w-5 text-primary" />
                  {booking.status === "pending" ? "Upcoming Booking" : "Active Session"} - {booking.slotId}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-6">
                    <div>
                      <p className="text-xs text-muted-foreground">Start Time</p>
                      <p className="font-medium text-foreground">{formatDateTime(booking.startTime)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">End Time</p>
                      <p className="font-medium text-foreground">{formatDateTime(booking.endTime)}</p>
                    </div>
                  </div>
                  <CountdownTimer
                    targetTime={booking.startTime}
                    label={booking.status === "pending" ? "Check-in starts in" : "Session ends in"}
                  />
                </div>
              </CardContent>
            </Card>
          ))}

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Calendar className="h-5 w-5 text-primary" />
              Booking History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Spinner className="h-8 w-8 text-primary" />
              </div>
            ) : bookings.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Calendar className="mb-4 h-12 w-12 text-muted-foreground" />
                <p className="text-lg font-medium text-foreground">No bookings yet</p>
                <p className="text-sm text-muted-foreground">Your booking history will appear here</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-muted-foreground">Booking ID</TableHead>
                      <TableHead className="text-muted-foreground">Slot</TableHead>
                      <TableHead className="text-muted-foreground">Start Time</TableHead>
                      <TableHead className="text-muted-foreground">End Time</TableHead>
                      <TableHead className="text-muted-foreground">Status</TableHead>
                      <TableHead className="text-muted-foreground">Deposit</TableHead>
                      <TableHead className="text-muted-foreground">Penalty</TableHead>
                      <TableHead className="text-right text-muted-foreground">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bookings.map((booking) => {
                      const status = statusConfig[booking.status];
                      const StatusIcon = status.icon;
                      const canCancel = booking.status === "pending";
                      const canReportFault = booking.status === "active" || booking.status === "pending";
                      const canCheckInLate = booking.status === "pending" && new Date(booking.startTime) < new Date();

                      return (
                        <TableRow key={booking.id} className="border-border">
                          <TableCell className="font-medium text-foreground">{booking.id}</TableCell>
                          <TableCell className="text-foreground">{booking.slotId}</TableCell>
                          <TableCell className="text-muted-foreground">{formatDateTime(booking.startTime)}</TableCell>
                          <TableCell className="text-muted-foreground">{formatDateTime(booking.endTime)}</TableCell>
                          <TableCell>
                            <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium", status.className)}>
                              <StatusIcon className="h-3 w-3" />
                              {status.label}
                            </span>
                          </TableCell>
                          <TableCell className="text-foreground">${booking.deposit}</TableCell>
                          <TableCell className={cn(booking.penalty ? "text-destructive font-medium" : "text-muted-foreground")}>
                            {booking.penalty ? `$${booking.penalty}` : "-"}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              {canCheckInLate && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="gap-1 border-warning text-warning hover:bg-warning/10"
                                  onClick={() => handleCheckInLate(booking)}
                                  disabled={actionLoading === booking.id}
                                >
                                  {actionLoading === booking.id ? (
                                    <Spinner className="h-3 w-3" />
                                  ) : (
                                    <AlertTriangle className="h-3 w-3" />
                                  )}
                                  Late Check-in
                                </Button>
                              )}
                              {canReportFault && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="gap-1"
                                  onClick={() => handleReportFault(booking)}
                                >
                                  <AlertTriangle className="h-3 w-3" />
                                  Report Fault
                                </Button>
                              )}
                              {canCancel && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="gap-1 border-destructive text-destructive hover:bg-destructive/10"
                                  onClick={() => handleCancel(booking.id)}
                                  disabled={actionLoading === booking.id}
                                >
                                  {actionLoading === booking.id ? (
                                    <Spinner className="h-3 w-3" />
                                  ) : (
                                    <XCircle className="h-3 w-3" />
                                  )}
                                  Cancel
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cancel Confirmation Dialog */}
        <AlertDialog open={cancelDialog.open} onOpenChange={(open) => setCancelDialog({ open, bookingId: null })}>
          <AlertDialogContent className="bg-card border-border">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-foreground">Cancel Booking?</AlertDialogTitle>
              <AlertDialogDescription className="text-muted-foreground">
                Are you sure you want to cancel this booking? Your deposit will be refunded.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="border-border">Keep Booking</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmCancel}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Cancel Booking
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* No-Show Confirmation Dialog */}
        <AlertDialog open={noShowDialog.open} onOpenChange={(open) => setNoShowDialog({ open, booking: null })}>
          <AlertDialogContent className="bg-card border-border">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-foreground">Late Check-in</AlertDialogTitle>
              <AlertDialogDescription className="text-muted-foreground">
                You are checking in late for your booking. A penalty of $0.50 per minute will be applied.
                {noShowDialog.booking && (
                  <span className="mt-2 block font-medium text-warning">
                    Current penalty: $15.00 (estimated)
                  </span>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="border-border">Go Back</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmNoShow}
                className="bg-warning text-warning-foreground hover:bg-warning/90"
              >
                Proceed with Late Check-in
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </main>
    </div>
  );
}

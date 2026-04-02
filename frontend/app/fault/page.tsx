"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  AlertTriangle,
  CheckCircle,
  Send,
  ArrowLeft,
  DollarSign,
  FileText,
} from "lucide-react";

function FaultPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    bookingId: "",
    slotId: "",
    driverId: "",
    description: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ message: string; refundAmount: number } | null>(null);

  useEffect(() => {
    // Pre-fill form from URL params
    const bookingId = searchParams.get("bookingId");
    const slotId = searchParams.get("slotId");
    const driverId = searchParams.get("driverId");

    if (bookingId || slotId || driverId) {
      setFormData((prev) => ({
        ...prev,
        bookingId: bookingId || prev.bookingId,
        slotId: slotId || prev.slotId,
        driverId: driverId || prev.driverId,
      }));
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Validate form
      if (!formData.bookingId || !formData.slotId || !formData.driverId || !formData.description) {
        throw new Error("Please fill in all required fields");
      }

      // Replace with actual API call:
      // const result = await reportFault(formData);
      
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      // Mock success response
      setSuccess({
        message: "Fault reported successfully. The slot has been marked as faulty.",
        refundAmount: 5.00,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit fault report");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleReset = () => {
    setFormData({
      bookingId: "",
      slotId: "",
      driverId: "",
      description: "",
    });
    setSuccess(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-6 gap-2 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        <Card className="border-border bg-card">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-warning/20">
                <AlertTriangle className="h-6 w-6 text-warning" />
              </div>
              <div>
                <CardTitle className="text-xl text-foreground">Report Charging Fault</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Report an issue with a charging station to receive a refund
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="flex flex-col items-center py-8 text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/20">
                  <CheckCircle className="h-8 w-8 text-success" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-foreground">Report Submitted</h3>
                <p className="mb-6 text-muted-foreground">{success.message}</p>
                
                <div className="mb-6 w-full max-w-xs rounded-lg bg-secondary/50 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-success" />
                      <span className="font-medium text-foreground">Refund Amount</span>
                    </div>
                    <span className="text-2xl font-bold text-success">${success.refundAmount.toFixed(2)}</span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Your deposit will be refunded within 3-5 business days
                  </p>
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={handleReset}>
                    Report Another
                  </Button>
                  <Button onClick={() => router.push("/bookings")}>
                    View Bookings
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="bookingId" className="text-foreground">
                      Booking ID <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="bookingId"
                      placeholder="e.g., BK001"
                      value={formData.bookingId}
                      onChange={(e) => handleChange("bookingId", e.target.value)}
                      className="bg-secondary border-border"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="slotId" className="text-foreground">
                      Slot ID <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="slotId"
                      placeholder="e.g., CS001"
                      value={formData.slotId}
                      onChange={(e) => handleChange("slotId", e.target.value)}
                      className="bg-secondary border-border"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="driverId" className="text-foreground">
                    Driver ID <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="driverId"
                    placeholder="Enter your driver ID"
                    value={formData.driverId}
                    onChange={(e) => handleChange("driverId", e.target.value)}
                    className="bg-secondary border-border"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-foreground">
                    <span className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Fault Description <span className="text-destructive">*</span>
                    </span>
                  </Label>
                  <Textarea
                    id="description"
                    placeholder="Please describe the issue you encountered with the charging station..."
                    value={formData.description}
                    onChange={(e) => handleChange("description", e.target.value)}
                    className="min-h-32 bg-secondary border-border resize-none"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Include details such as error messages, physical damage, or unexpected behavior
                  </p>
                </div>

                <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
                  <h4 className="mb-2 font-medium text-foreground">What happens next?</h4>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary" />
                      Your fault report will be reviewed by our support team
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary" />
                      The charging slot will be marked as faulty and taken offline
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary" />
                      Your deposit will be refunded automatically
                    </li>
                  </ul>
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => router.back()}
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
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Submit Report
                      </>
                    )}
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function FaultPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    }>
      <FaultPageContent />
    </Suspense>
  );
}

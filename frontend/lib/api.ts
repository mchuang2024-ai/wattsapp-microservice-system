// API Configuration - Update this to point to your backend
// When running locally, use localhost with exposed ports from docker-compose
// When running inside Docker, set NEXT_PUBLIC_* env vars to use service names
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5011';
const BOOKING_SERVICE_URL = process.env.NEXT_PUBLIC_BOOKING_URL || 'http://localhost:5002';
const DRIVER_SERVICE_URL = process.env.NEXT_PUBLIC_DRIVER_URL || 'http://localhost:5001';
const VIEW_SLOTS_SERVICE_URL = process.env.NEXT_PUBLIC_VIEW_SLOTS_URL || 'http://localhost:5006';
const HANDLE_NOSHOW_URL = process.env.NEXT_PUBLIC_HANDLE_NOSHOW_URL || 'http://localhost:5100';
const REPORT_FAULT_URL = process.env.NEXT_PUBLIC_REPORT_FAULT_URL || 'http://localhost:5010';

// Types
export interface ChargingSlot {
  id: string;
  type: 'Fast' | 'Slow';
  status: 'available' | 'occupied' | 'faulty' | 'maintenance';
  deposit: number;
  location: string;
  powerOutput: string;
  pricePerKwh: number;
  date: string;
  startTime: string;
  endTime: string;
}

export interface Booking {
  id: string;
  driverId: string;
  chargerId: string;
  slotId: string;
  startTime: string;
  endTime: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled' | 'no-show' | 'late';
  deposit: number;
  createdAt: string;
  checkedInAt?: string;
  penalty?: number;
}

export interface Driver {
  id: string;
  name: string;
  email: string;
  lateCount: number;
  penaltyScore: number;
  isBlocked: boolean;
}

export interface FaultReport {
  bookingId: string;
  slotId: string;
  driverId: string;
  description: string;
}

export interface BookingRequest {
  driverId: string;
  chargerId: string;
  slotId: string;
  startTime: string;
  endTime: string;
  deposit: number;
}

function normalizeBooking(raw: any): Booking {
  return {
    id: String(raw.bookingID ?? raw.id ?? raw.data?.bookingID ?? raw.data?.id ?? ''),
    driverId: String(raw.driverID ?? raw.driverId ?? raw.data?.driverID ?? raw.data?.driverId ?? ''),
    chargerId: String(raw.chargerID ?? raw.chargerId ?? raw.slotID ?? raw.slotId ?? ''),
    slotId: String(raw.slotID ?? raw.slotId ?? raw.chargerID ?? raw.chargerId ?? ''),
    startTime: raw.startTime ?? raw.data?.startTime ?? '',
    endTime: raw.endTime ?? raw.data?.endTime ?? '',
    status: (raw.status ?? raw.data?.status ?? 'pending') as Booking['status'],
    deposit: Number(raw.depositAmount ?? raw.deposit ?? 5),
    createdAt: raw.createdAt ?? raw.data?.createdAt ?? new Date().toISOString(),
    checkedInAt: raw.checkedInAt ?? raw.data?.checkedInAt,
    penalty: raw.minsLate ?? raw.data?.minsLate,
  };
}

function normalizeSlot(raw: any): ChargingSlot {
  return {
    id: String(raw.slotID ?? raw.id ?? 'unknown'),
    type: (raw.type ?? 'Fast') as ChargingSlot['type'],
    status: (raw.status ?? 'available') as ChargingSlot['status'],
    deposit: Number(raw.deposit ?? 5),
    location: String(raw.location ?? 'Unknown location'),
    powerOutput: String(raw.powerOutput ?? 'Unknown'),
    pricePerKwh: Number(raw.pricePerKwh ?? 0.0),
    date: String(raw.date ?? ''),
    startTime: String(raw.startTime ?? ''),
    endTime: String(raw.endTime ?? ''),
  };
}

// API Functions
export async function fetchSlots(date: string, driverId: string): Promise<ChargingSlot[]> {
  const query = new URLSearchParams({ date, driverID: driverId });
  const response = await fetch(`${VIEW_SLOTS_SERVICE_URL}/view-slots?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch slots');
  const payload = await response.json();
  return (payload.slots ?? []).map(normalizeSlot);
}

export async function fetchSlotsByFilter(params: {
  location?: string;
  date?: string;
  driverId?: string;
  startTime?: string;
  endTime?: string;
}): Promise<ChargingSlot[]> {
  if (!params.date || !params.driverId) {
    throw new Error('view-slots requires date and driverId');
  }
  const query = new URLSearchParams({ date: params.date, driverID: params.driverId });
  const response = await fetch(`${VIEW_SLOTS_SERVICE_URL}/view-slots?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to fetch slots');
  const payload = await response.json();
  let slots: ChargingSlot[] = (payload.slots ?? []).map(normalizeSlot);

  // Client-side time filtering (API returns all 1-hour blocks for the day)
  if (params.startTime) {
    const filterStart = params.startTime; // "HH:MM"
    slots = slots.filter(s => {
      const slotHour = s.startTime.split(' ')[1]?.slice(0, 5) ?? '';
      return slotHour >= filterStart;
    });
  }
  if (params.endTime) {
    const filterEnd = params.endTime; // "HH:MM"
    slots = slots.filter(s => {
      const slotEndHour = s.endTime.split(' ')[1]?.slice(0, 5) ?? '';
      return slotEndHour <= filterEnd;
    });
  }

  return slots;
}

export async function fetchDriverLateCount(driverId: string): Promise<{ lateCount: number; penaltyScore: number; isBlocked: boolean }> {
  const response = await fetch(`${DRIVER_SERVICE_URL}/drivers/${driverId}`);
  if (!response.ok) throw new Error('Failed to fetch driver info');
  const payload = await response.json();
  const rawDriver = payload.data ?? {};
  const lateCount = Number(rawDriver.late_count ?? 0);
  return {
    lateCount,
    penaltyScore: lateCount * 10,
    isBlocked: lateCount >= 5,
  };
}

export async function fetchPricingDeposit(): Promise<{ deposit: number }> {
  return { deposit: 5 };
}

export async function createBooking(data: BookingRequest): Promise<Booking> {
  const payload = {
    driverID: data.driverId,
    chargerID: data.chargerId || data.slotId,
    starttime: data.startTime,
    endtime: data.endTime,
    deposit: data.deposit,
  };
  const response = await fetch(`${API_BASE_URL}/create-booking`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to create booking');
  }
  const result = await response.json();
  return normalizeBooking({
    bookingID: result.bookingID,
    status: 'confirmed',
    startTime: data.startTime,
    endTime: data.endTime,
    driverID: data.driverId,
    chargerID: data.chargerId || data.slotId,
    slotID: data.slotId || data.chargerId,
    deposit: data.deposit,
    createdAt: new Date().toISOString(),
  });
}

export async function fetchBookings(driverId?: string): Promise<Booking[]> {
  const response = await fetch(`${BOOKING_SERVICE_URL}/booking`);
  if (!response.ok) throw new Error('Failed to fetch bookings');
  const payload = await response.json();
  const bookings = (payload.data?.bookings ?? []) as any[];
  const normalized = bookings.map(normalizeBooking);
  return driverId ? normalized.filter((booking) => booking.driverId === String(driverId)) : normalized;
}

export async function handleNoShow(bookingId: string, driverId?: string, lateCheckIn = true): Promise<any> {
  const body: any = { bookingID: bookingId };
  if (driverId) body.driverID = driverId;
  body.lateCheckIn = lateCheckIn ? 'True' : 'False';
  const response = await fetch(`${HANDLE_NOSHOW_URL}/handle-noshow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to handle no-show');
  }
  return response.json();
}

export async function cancelBooking(bookingId: string): Promise<{ message: string }> {
  const response = await fetch(`${BOOKING_SERVICE_URL}/booking/${bookingId}/cancel`, {
    method: 'PUT',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to cancel booking');
  }
  return response.json();
}

export async function checkInBooking(bookingId: string): Promise<Booking> {
  const response = await fetch(`${BOOKING_SERVICE_URL}/booking/${bookingId}/checkin`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ checkinTime: new Date().toISOString().slice(0, 19).replace('T', ' ') }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to check in');
  }
  const payload = await response.json();
  return normalizeBooking(payload.data ?? payload);
}

export async function reportFault(data: FaultReport): Promise<{ message: string; refundAmount?: number }> {
  const response = await fetch(`${REPORT_FAULT_URL}/reportfault`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bookingID: data.bookingId,
      slotID: data.slotId,
      driverID: data.driverId,
      description: data.description,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to report fault');
  }
  return response.json();
}

export async function fetchLocations(): Promise<string[]> {
  return [
    'Downtown Mall',
    'City Center',
    'Shopping District',
    'Highway Rest Stop',
    'University Campus',
    'Sports Complex',
  ];
}

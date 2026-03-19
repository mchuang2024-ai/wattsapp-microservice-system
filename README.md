# wattsapp-microservice-system
Wattsapp is a system designed to enable easy access to electronic vehicle charging in Singapore. This system will utilize microservices architecture and build various microservices for the app.

Singapore targets 100,000 EVs by 2030 under the National Green Plan, yet charging infrastructure lags behind. Drivers face fragmented apps, uncertain slot availability, and 20–30 minute waits at hubs like Sengkang — not from a shortage of chargers, but a lack of coordination between parking, charging, and billing systems.

PulsePark solves this with a unified, event-driven enterprise solution built on a Microservices Architecture. It integrates slot management, EV charging session control, and dynamic billing into a single platform — assembling loosely-coupled atomic and composite microservices across a layered SOA to fully automate workflows like no-show handling, waitlist promotion, and overstay penalty enforcement.

We cover 3 user scenarios:

1. Slot Booking — a driver books and pays a deposit for a charging slot
2. No-Show Handling — a grace period, deposit forfeiture, tiered penalties, and automatic waitlist promotion
3. Overstay Penalty — dynamic billing, and refunds for affected next users
   
Across all scenarios, our solution showcases HTTP and AMQP communication, Docker Compose deployment, service reuse (Payment service reused 4 times), orchestration, and Beyond-the-Labs features including delayed AMQP messaging and the Telegram Bot API.

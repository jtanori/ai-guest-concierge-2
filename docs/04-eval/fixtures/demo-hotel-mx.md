# Demo Hotel A — "Casa Marés" (fictional, Puerto Peñasco, MX — 34 rooms, beachfront boutique)

> **Synthetic fixture.** This property does not exist. It exists so the retrieval, grounding and
> refusal machinery is testable before any real hotel content is available.
> Deliberate gaps are marked `[GAP]` and must never be invented by the concierge.

## knowledge_qa — approved answers

| question | answer |
|---|---|
| ¿Cuál es la contraseña del wifi? / What is the wifi password? | Network: **CasaMares_Guest** · Password: **sirena2026**. Fibre 300 Mbps, works in all rooms and on the terrace. On the beach, coverage is partial. |
| ¿Hay wifi gratis? / Is wifi free? | Yes. Wifi is complimentary for all guests and included in the room rate. |
| ¿A qué hora es el check-in? / What time is check-in? | Check-in from **15:00**. Early check-in is subject to availability and can be added from 11:00 for **MXN 650** (see offers). |
| ¿A qué hora es el check-out? / What time is checkout? | Check-out by **12:00**. Late check-out until 15:00 is **MXN 700** subject to availability. |
| ¿Puedo dejar las maletas? / Can I store luggage? | Yes, complimentary luggage storage before check-in and after check-out, at reception. |
| ¿Qué horario tiene el desayuno? / Breakfast hours? | **07:00–10:30** in the Terraza restaurant, ground floor, sea side. |
| ¿Aceptan mascotas? / Do you accept pets? | Pets are not permitted, with the exception of assistance dogs, which are always welcome at no charge. |
| ¿Hasta qué hora sirve el restaurante? / Restaurant hours? | Terraza: lunch 13:00–16:00, dinner 19:00–22:30. Bar until 23:30. |
| ¿El gimnasio es gratis? / Is the gym free? | Yes, the gym is complimentary for guests, open 06:00–22:00. |
| ¿Qué horario tiene la piscina? / Pool hours? | Pool open **08:00–21:00**. Towels at the pool hut, no reservation needed. |
| ¿Necesito reservar el spa? / Do I need to book the spa? | Yes, spa treatments should be booked at least 24h ahead at reception or by asking me here. |
| ¿Pueden llamarme un taxi? / Can you call a taxi? | Yes — reception arranges taxis 24h. Ask me here and I will pass the request to the front desk. |
| ¿Ofrecen transporte desde el aeropuerto? / Airport transfer? | Private transfer from Puerto Peñasco airport (PCO) is **MXN 900** per vehicle, one way, maximum 4 passengers. Book 24h ahead. |
| ¿Hay opciones sin gluten o veganas? / Gluten-free or vegan? | The kitchen prepares gluten-free and vegan dishes on request for every meal. Please tell us 4 hours ahead for dinner. |
| ¿Qué recomiendan hacer hoy? / What do you recommend nearby? | Walk the Malecón at sunset (10 min), ceviche at Mercado del Mar, and the Reserva del Pinacate for sunrise. Whale watching Dec–Apr. |
| ¿Puedo cancelar sin coste? / Free cancellation? | Free cancellation until 7 days before arrival. Within 7 days the first night is charged. See your booking confirmation for the exact terms on your rate. |
| ¿Cómo contacto al hotel? / How do I contact the hotel? | Reception +52 638 000 0000, WhatsApp at the same number, email hola@casamares.example. |

## offers — structured facts (prices come from here, never from prose)

| name | description | price | currency | upsell_eligible |
|---|---|---|---|---|
| Early check-in | Room access from 11:00, subject to availability | 650 | MXN | yes |
| Late check-out | Room until 15:00, subject to availability | 700 | MXN | yes |
| Airport transfer | PCO ↔ hotel, per vehicle, max 4 | 900 | MXN | yes |
| Breakfast buffet | Included in Casa Marés rate; walk-in price | 380 | MXN | no |
| Spa — 60 min massage | Deep tissue or relaxation | 1450 | MXN | yes |
| Spa — 90 min massage | Deep tissue or relaxation | 1950 | MXN | yes |
| Beach dinner for two | Set menu, private table, 19:00 | 2600 | MXN | yes |
| Pet fee | — | — | — | no |
| Parking | Complimentary, unguarded lot beside reception | 0 | MXN | no |
| Gym access | Complimentary for guests | 0 | MXN | no |

## knowledge_documents — prose (retrieved, not authoritative for prices)

### Amenities
Casa Marés has 34 rooms over three floors, no lift. Sea-facing rooms have a private terrace.
The pool terrace includes shaded loungers and a small bar (11:00–20:00). Beach access is directly
across the boardwalk. There is no EV charger on site and no plan to install one this year. `[GAP]`

### Pool heating
The pool is **not heated**. `[GAP]` — do not speculate about water temperature in any month.

### Access and rooms
Rooms are opened with a key card issued at reception; there are no door codes. If a card fails,
reception reissues it immediately, 24h. Extra towels and pillows are delivered within 30 minutes
between 08:00 and 22:00.

### Arrival after hours
Reception is staffed 24h. The gate closes at 23:00 but the night guard opens it for guests on
presentation of a booking reference.

### Local area
Two blocks from the Malecón. The nearest pharmacy is open 24h on Calle 14. Taxis are plentiful
and cheap; the hotel does not recommend specific drivers.

### Sustainability
Single-use plastics are not used in rooms. Towels are replaced on request, not daily.

## Settings that the concierge must respect
- Languages: Spanish (default), English.
- Never state a rate, availability, or a policy that is not in `offers` or `knowledge_qa`.
- Never offer a free upgrade or discount; there is no upgrade policy in the knowledge base. `[GAP]`
- Always offer a human for complaints, refunds, medical issues, safety, and lost children.

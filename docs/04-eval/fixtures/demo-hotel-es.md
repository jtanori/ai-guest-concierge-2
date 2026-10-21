# Demo Hotel B — "Hotel Serrano 12" (fictional, Sevilla, ES — 48 rooms, city boutique)

> **Synthetic fixture.** Does not exist. Second property exists to prove the pipeline is
> tenant-scoped and that the same 30 questions behave differently against different content.

## knowledge_qa — approved answers

| question | answer |
|---|---|
| ¿Cuál es la contraseña del wifi? / Wifi password? | Network **Serrano12**, password **naranja2026**. Fibre in all rooms and the patio. |
| ¿El wifi es gratis? / Is wifi free? | Complimentary, included in every rate. |
| ¿A qué hora es el check-in? / Check-in time? | From **14:00**. Early check-in from 11:00 for **EUR 35**, subject to availability. |
| ¿A qué hora es el check-out? / Check-out time? | By **11:30**. Late check-out until 14:00 for **EUR 40**, subject to availability. |
| ¿Puedo dejar las maletas? / Luggage storage? | Yes, free before check-in and after check-out. |
| Desayuno: horario y lugar / Breakfast hours and where? | **07:30–11:00**, Patio Andaluz, at the back of the lobby. |
| ¿El desayuno está incluido? / Is breakfast included? | Included in the Serrano rate; not included in the Basic rate. |
| ¿Precio del desayuno? / Breakfast price? | **EUR 19** per person if not included in your rate. |
| Restaurante: horario / Restaurant hours? | Tapas bar 12:30–16:00 and 20:00–23:30. Kitchen closes 23:00. |
| ¿Hay opciones veganas? / Vegan options? | Yes — vegan and gluten-free tapas are marked on the menu; the kitchen can adapt most dishes. |
| ¿Tienen parking? / Parking? | Public garage **Garaje Alcázares**, 180 m away, **EUR 26** per 24h. No hotel garage. |
| ¿Se puede cargar coche eléctrico? / EV charging? | No chargers on site; the Alcázares garage has two Type-2 points. |
| ¿Ofrecen transporte del aeropuerto? / Airport transfer? | Private transfer from Sevilla (SVQ) **EUR 45** per car, one way. Book 24h ahead. |
| ¿Hay taxi a las 6:00? / Taxi at 6am? | Reception books taxis 24h; say the time and we will arrange it. |
| Piscina: horario / Pool hours? | Rooftop plunge pool and solarium open **10:00–20:00** (May–October). |
| ¿La piscina está climatizada? / Is the pool heated? | The pool is **not heated**; it closes outside May–October. |
| Gimnasio / Gym? | Small gym, complimentary, 06:00–23:00. |
| Spa: masaje y precio / Massage and price? | Treatments are not offered on site. We can arrange a partner spa 300 m away, from **EUR 85** for 50 minutes. |
| ¿Aceptan mascotas? / Pets? | Small pets up to 8 kg welcome, **EUR 25** per stay. Assistance dogs always free. |
| ¿Puedo cancelar sin coste? / Free cancellation? | Free cancellation until 48h before arrival on flexible rates; non-refundable rates cannot be cancelled. |
| ¿Qué recomiendan? / What do you recommend? | Alcázar (8 min walk), Triana for dinner, Setas at dusk. Flamenco at Casa de la Memoria, 19:30. |
| Contacto / Contact | Reception +34 954 000 000, email hola@serrano12.example. |

## offers — structured facts

| name | description | price | currency | upsell_eligible |
|---|---|---|---|---|
| Early check-in | Access from 11:00, subject to availability | 35 | EUR | yes |
| Late check-out | Room until 14:00, subject to availability | 40 | EUR | yes |
| Airport transfer | SVQ ↔ hotel, per car | 45 | EUR | yes |
| Breakfast (if not in rate) | Per person | 19 | EUR | no |
| Public parking (Alcázares) | 180 m from hotel, per 24h | 26 | EUR | no |
| Pet fee | Up to 8 kg, per stay | 25 | EUR | no |
| Partner spa — 50 min | 300 m from hotel | 85 | EUR | yes |
| Rooftop private dinner | Set menu for two, 20:00 | 140 | EUR | yes |
| Gym | Complimentary | 0 | EUR | no |

## knowledge_documents — prose

### Building and access
The building is a restored 19th-century townhouse over four floors **with a lift**. Rooms are
opened with a key card; there are no door codes. Cards are reactivated at reception 24h.

### Rooms
Standard rooms face the interior patio; Deluxe rooms face Calle Serrano. Interior rooms are
quieter. Extra towels and pillows within 30 minutes between 08:00 and 23:00.

### Pool season
The rooftop pool operates **May to October only**. `[GAP]` — exact opening date each year is set
by the building committee and is not known in advance; never promise a specific opening date.

### Accessibility
Lift to all floors; two adapted rooms; step-free entrance from Calle Serrano. `[GAP]` — no
information about adapted bathroom dimensions; refer to reception.

### Neighbourhood
Alcázar 8 minutes on foot, Cathedral 12. The street is pedestrianised; taxis stop at the corner
of Calle Mateos Gago. Nearest 24h pharmacy: Calle Prado.

### Housekeeping
Daily service between 09:00 and 15:00. Turndown on request. Laundry returned within 24h,
collected before 10:00.

## Settings that the concierge must respect
- Languages: Spanish (default), English.
- Prices only from `offers`. Never invent availability, pool opening dates, or spa prices.
- No upgrade policy exists in the knowledge base. `[GAP]` — offer to ask reception instead.
- Escalate immediately: complaints, refunds, medical, safety, lost children.

-- Supplier overlap and canonicalization rate
SELECT
    COUNT(DISTINCT sh.id) AS total_supplier_hotels,
    COUNT(DISTINCT sh.canonical_hotel_id) AS canonical_hotels,
    ROUND(COUNT(DISTINCT sh.id)::numeric / NULLIF(COUNT(DISTINCT sh.canonical_hotel_id), 0), 2)
        AS listings_per_canonical,
    ROUND((1 - COUNT(DISTINCT sh.canonical_hotel_id)::numeric / NULLIF(COUNT(DISTINCT sh.id), 0)) * 100, 2)
        AS duplicate_consolidation_pct
FROM supplier_hotels sh
WHERE sh.match_status IN ('AUTO_MATCHED', 'MANUAL_OVERRIDE');

-- Rate competitiveness by supplier
WITH market AS (
    SELECT sh.canonical_hotel_id, MIN(r.base_net_rate + r.tax_and_fees) AS lowest_rate
    FROM supplier_rooms r
    JOIN supplier_hotels sh ON sh.id = r.supplier_hotel_id
    WHERE r.is_available
    GROUP BY sh.canonical_hotel_id
)
SELECT s.code, COUNT(r.id) AS available_quotes,
       COUNT(*) FILTER (WHERE r.base_net_rate + r.tax_and_fees = m.lowest_rate) AS cheapest_quotes,
       ROUND(AVG(r.base_net_rate + r.tax_and_fees - m.lowest_rate), 2) AS average_premium
FROM supplier_rooms r
JOIN supplier_hotels sh ON sh.id = r.supplier_hotel_id
JOIN suppliers s ON s.id = sh.supplier_id
JOIN market m ON m.canonical_hotel_id = sh.canonical_hotel_id
WHERE r.is_available
GROUP BY s.code
ORDER BY cheapest_quotes DESC;

-- Impression to booking conversion funnel
SELECT entity_type,
       COUNT(*) FILTER (WHERE event_type = 'IMPRESSION') AS impressions,
       COUNT(*) FILTER (WHERE event_type = 'DETAIL_VIEW') AS detail_views,
       COUNT(*) FILTER (WHERE event_type = 'BOOKING_INTENT') AS booking_intents,
       COUNT(*) FILTER (WHERE event_type = 'BOOKED') AS bookings,
       ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'DETAIL_VIEW') /
             NULLIF(COUNT(*) FILTER (WHERE event_type = 'IMPRESSION'), 0), 2) AS ctr_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'BOOKED') /
             NULLIF(COUNT(*) FILTER (WHERE event_type = 'IMPRESSION'), 0), 2) AS booking_conversion_pct
FROM ranking_conversion_telemetry
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY entity_type;

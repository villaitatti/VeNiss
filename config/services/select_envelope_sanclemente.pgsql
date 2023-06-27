SELECT DISTINCT a.identifier, a.t, a.z, c.start, c.end , a.geometry
FROM PUBLIC.veniss_data AS a
JOIN PUBLIC.feature_years AS b ON a.identifier = b.identifier
JOIN PUBLIC.years_dates AS c ON b."year" = c."year"
WHERE b."year" IS NOT NULL
AND ST_WITHIN(geometry, 
	ST_MakeEnvelope(1372486.572254345, 5685752.99679293, 1373886.2646889214, 5687304.5202712575, 3857)) 
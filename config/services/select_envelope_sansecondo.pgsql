SELECT DISTINCT a.identifier, a.t, a.z, b.y, a.geometry
FROM PUBLIC.veniss_data AS a
JOIN PUBLIC.feature_years AS b
ON a.identifier = b.identifier
WHERE ST_WITHIN(geometry, 
	ST_MakeEnvelope(1368358.959761288, 5692238.026840036, 1371414.0522355612, 5693523.1243780805, 3857))
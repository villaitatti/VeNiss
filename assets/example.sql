select distinct "BW_ID" as subject, ST_AsText(geo) as wkt 
from archipelago_table 
where ST_WITHIN(geo, ST_MakeEnvelope(
	1368358.959761288, 
	5692238.026840036, 
	1371414.0522355612, 
	5693523.1243780805, 
	3857)
)
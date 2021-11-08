DROP TABLE IF EXISTS sansecondo_tmp;
CREATE TABLE sansecondo_tmp AS
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1500
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1500
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1697
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1697
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1717
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1717
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1789
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1789
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1839
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1839
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1850
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1850
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1852
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1852
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_1945
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_1945
UNION 
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_buildings_2019
UNION
SELECT DISTINCT "BW_ID" as bw_id, geometry as wkt 
FROM sansecondo_island_2019;

DROP TABLE IF EXISTS sansecondo;
CREATE TABLE sansecondo AS
SELECT DISTINCT * FROM sansecondo_tmp;

DROP TABLE sansecondo_tmp;


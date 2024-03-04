# VeNiss

## How to commit

The **master** branch is read-only. PRs are needed to add new functionalities and resolve bugs. Every PR is meant to document the reason why we updated the system to the new version

## Security

In development mode, all the passwords needs to be passed as JAVA OPTS. Add the following code to the `build.gradle` file, replacing the passwords:

```
"-Dsecret.geo.username=DB_USERNAME",
"-Dsecret.geo.password=DB_PASSWORD",

"-Dsecret.default.username=ARCHIPELAGO_USERNAME",
"-Dsecret.default.password=ARCHIPELAGO_PASSWORD",

"-Dconfig.proxy.mapbox.tokenQueryValue=API_KEY",
```

while on config files set: `${default.username}`

## Default.ttl

For development, set username and password and then move this file to ./config/repositories/default.ttl. Or follow

```
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix mph: <http://www.researchspace.org/resource/system/repository#> .
@prefix ephedra: <http://www.researchspace.org/resource/system/ephedra#> .
@prefix fedsail: <http://www.openrdf.org/config/sail/federation#> .
@prefix sparqlr: <http://www.openrdf.org/config/repository/sparql#> .
[] a rep:Repository;
  rep:repositoryID "default";
  rdfs:label "Default HTTP SPARQL Repository";
  rep:repositoryImpl [
      rep:repositoryType "researchspace:SPARQLBasicAuthRepository";
      sparqlr:query-endpoint <https://veniss.net/sparql>;
      mph:quadMode true;
      mph:writable true;
      mph:username "${default.username}" ;
      mph:password "${default.password}" ;
    ] .
```

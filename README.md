# archipelago

## How to commit

The **master** branch is read-only. PRs are needed to add new functionalities and resolve bugs. Every PR is meant to document the reason why we updated the system to the new version

## Security

In development mode, all the passwords needs to be passed as JAVA OPTS. Add the following code to the `build.gradle` file, replacing the passwords:

```
"-Dsecret.geo.username=DB_USERNAME",
"-Dsecret.geo.password=DB_PASSWORD",

"-Dsecret.default.username=ARCHIPELAGO_USERNAME",
"-Dsecret.degault.password=ARCHIPELAGO_PASSWORD",

"-Dconfig.proxy.mapbox.tokenQueryValue=API_KEY",
```

# Structure

To generate a site, you need to set up a directory with the following
structure:

```
/
/places.yaml
/trips
```

## Places

All your places referenced in trips must be in a `places.yaml` file.

```yaml
---
Luton-Airport: W110273499
Paris-CDG: W294032205
```


## Trips

Your trips belong in a directory called `trips`. Each trip is a Markdown file
with journey information in a front matter block.

The front matter block looks like this:

```
===
From Luton-Airport on 2018-07-03
To Paris-CDG by plane

From Paris-Montparnasse on 2018-07-06
To Toulouse-Matabiau by train
To Rodez-Gare

From Camares on 2018-07-11
To Toulouse-Blagnac by car
To Luton-Airport by train
===
```

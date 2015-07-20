## Specification ##

```
at TIME {
}

repeat REPETITON {
}

TIME  = PHASE [(+|-) TIME] | TIME
PHASE = sunset | dusk | night | dawn | sunrise
TIME  = 00h[:00m] -> 24h[:00m]

REPETITION = forever | d MULTIPLIER
MULTIPLIER = days | weeks | months

```

## Example ##

Run a program today and tomorrow during the night with calibrations 2 hours before sunset.

```

repeat 2 days {

  at dusk - 2h {

    calibration {
     BIAS      10                                           # 10 bias (exptime and filter useless)
     DOME_FLAT 10*(U:10:1 ,B:20:1, V:10:1 ,R:10:1 ,I:10:1)  # [UBVRI, UBVRI, ...]
     DOME_FLAT 1 *(U:10:10,B:20:10,V:10:10,R:10:10,I:10:10) # [UUUUUUUUUU, BBBBBBBBBB, ...]   
    }

  }

  at night {
    science {
      20:00:00 -22:30:00 2000 object_name 10*(B:10:1 ,V:10:1 ) # point to the given ra, dec, epoch and  object name, [BV, BV, ...]
      M25                                 1 *(B:10:10,V:10:10) # point to the given object name, [BBBBBBBBBB, VVVVVVVVVV]
  }

}

```
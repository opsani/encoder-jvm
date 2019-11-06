# encoder-jvm
Plug-in JVM arguments encoder for servo

# Usage
When you will be packaging an adjust driver with JVM settings encoder, please copy `encoders/jvm.py` to your final package's `encoders/` folder. 
Follow further packaging steps you can find in the repo `opsani/servo`.

# Available settings and their defaults

```yaml
MaxHeapSize:
  min: 0.5
  step: 1
  unit: 'GiB'

InitialHeapSize:
  min: 0.5
  step: 1
  unit: 'GiB'

InitialEdenHeapSize:
  min: 0.03125
  step: 0.03125
  unit: 'GiB'

GCTimeRatio:
  min: 9
  max: 99
  step: 10
  unit: ''

GCType:
  values:
    - ParNewGC
    - G1GC
    - ParallelOldGC
    - ConcMarkSweepGC

CMSInitiatingOccupancyFraction:
  min: 50
  max: 95
  step: 1
  default: 92

AlwaysPreTouch:
  default: False

CMSParallelRemarkEnabled:
  default: False

CMSScavengeBeforeRemark:
  default: False

ExplicitGCInvokesConcurrent:
  default: False

ParallelRefProcEnabled:
  default: False

ScavengeBeforeFullGC:
  default: False

UnlockExperimentalVMOptions:
  default: False

UseCGroupMemoryLimitForHeap:
  default: False

UseCMSInitiatingOccupancyOnly:
  default: False

UseStringDeduplication:
  default: False

G1NewSizePercent:
    min = 0
    max = 100
    step = 1
    default = 5

G1ReservePercent:
    min = 0
    max = 100
    step = 1
    default = 10

G1MixedGCLiveThresholdPercent:
    min = 0
    max = 100
    step = 1
    default = 65

MaxGCPauseMillis:
    min = 1
    max = 1000
    step = 1
    default = 200

NewRatio:
    min = 1
    max = 99
    step = 1
    default = 2

SurvivorRatio:
    min = 1
    max = 99
    step = 1
    default = 8

TargetSurvivorRatio:
    min = 9
    max = 99
    step = 1
    default = 50

StackShadowPages:
    min = 0
    max = 100
    step = 1
    default = 20
```

## Important notes on configuring settings

For `GCTimeRatio` configurable options `min`, `max` and `step` can only be within the range of default values. Where `step` can be only a multiple of a default step value. Ex. if default `step` is 1.5, configured `step` has to be one of its multiples: `3`, `4.5`, `6` and so on.

For `GCType` configurable option `values` can only contain a subset of defaults.

For `MaxHeapSize` `InitialHeapSize` and `InitialEdenHeapSize` option `max` is unknown and has to be configured by the user.

For all the `range` settings option `step` has to allow the setting to get from `min` to `max` in equal incremental steps. Ex. if `min` is 7 and `max` is 32, step can be only `1`, `5` or `25`.  

All the provided settings above will be likely configurable under the key `settings` of the driver configuration file in a particular place of use of the JVM arguments encoder. Ex. for `servo-k8s` driver you can set them at `command: encoder: settings` in a particular component in the driver config file.

# How to run tests
Prerequisites:
* Python 3.5 or higher
* PyTest 4.3.0 or higher

Follow these steps:
1. Pull the repository
2. Copy `base.py` from `https://github.com/opsani/servo/tree/master/encoders` to folder `encoders/`
3. Run `pytest` from the root folder

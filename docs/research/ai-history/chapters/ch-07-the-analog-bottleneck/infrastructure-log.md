# Infrastructure Log: Chapter 7 — The Analog Bottleneck

Each entry traces to a verified anchor in `sources.md`.

## Elmer and Elsie — the prototype build (1948 – 1949)

### Sensors

- **One photoelectric cell** ("photo-electric cell" / "eye"), fitted with a shroud that "blocks the entry of light from all directions except the front of the cell" so that the direction of gaze is always aligned with the direction of motion. (Walter 1950, p. 42 — sensor list. Holland 2003, pp. 2098–2099 — shroud and gaze-alignment detail.) **Green.**
- **One touch / bump sensor.** Implemented as a single rubber mounting that holds the shell, with a ring contact closed when the shell is deflected by gravity (slope) or contact (touch). (Walter 1950, p. 44 — multivibrator description; Holland 2003, p. 2099 — rubber-mount mechanism.) **Green.**

### "Brain" — active electronic components

- **Two miniature radio tubes** (thermionic valves / vacuum tubes), arranged as a two-stage amplifier. The photoelectric cell controls the first-stage current; the second-stage current drives two relay coils (RL1 and RL2) which switch the steering motor and drive motor between off / half / full power. (Walter 1950, p. 42 — count and arrangement; Holland 2003, pp. 2099–2100 — circuit-diagram explanation.) **Green.**
- **Two relays (RL1 and RL2).** RL1 is connected to the power line through the headlamp and a resistor and so can deliver only about half the current of RL2, which is connected directly. (Holland 2003, p. 2100 — verbatim circuit description.) **Green.**

### Effectors

- **One drive motor** for "crawling" forward. (Walter 1950, p. 42 — verbatim "two effectors or motors, one for crawling and the other for steering.") **Green.**
- **One steering / scanning motor** that rotates the entire structure (drive wheel + photocell) about the vertical axis. The same spindle supports the photocell so that the eye is always "looking" in the direction in which the model is moving (Walter calls this "scanning"). (Walter 1950, p. 43 — scanning behaviour; Holland 2003, pp. 2099–2100 — vertical-axis rotation detail.) **Green.**

### Mechanical structure

- **Translucent plastic shell** that protects the electronics and acts as the contact-bearing element for the touch sensor. (Walter 1950, p. 42 — sketch captions; Holland 2003 p. 2098–2099 — figure 3 labelled diagram.) **Green.**
- **Headlamp** (a torch bulb) connected in series with the steering motor, so that the headlamp is lit only when the steering motor is turned on. The headlamp is visible through a hole in the shell from the front. This indicator was added partway through the project (Walter 1950, p. 45 — "When the models were first made, a small light was connected in the steering-motor circuit to act as an indicator showing when the motor was turned off and on. It was soon found that this light endowed the machines with a new mode of behavior") and is what makes the mirror-flicker / two-tortoise interaction scene possible. (Holland 2003, p. 2099.) **Green.**
- **Three wheels.** A single front drive wheel that also rotates about the vertical axis; two rear wheels that are not driven. (Holland 2003, p. 2099.) **Green.**
- **Gearwheels** salvaged from old gas meters and alarm clocks. (Holland 2003, p. 2092 — verbatim.) **Green.** This is the piece of evidence that anchors the "chronic unreliability" narrative for Elmer and Elsie specifically.

### Power

- **One miniature six-volt storage battery** ("a miniature six-volt storage battery, which provides both A and C current for the tubes and the current for the motors") plus **one miniature hearing-aid B battery**. (Walter 1950, p. 42 — verbatim.) **Green.** The chapter must not collapse this into "a six-volt battery" — Walter's description names two distinct power sources and the two-battery layout is part of why the build was constrained.

### Charging infrastructure

- **A "hutch" or "kennel"** containing both a battery charger and a 20-watt lamp. The lamp acts as a sufficiently bright light that, when the storage battery has run down and the amplifier becomes hypersensitive, the kennel-light becomes attractive instead of repellent. (Walter 1950, p. 43 — verbatim "battery charger and a 20-watt lamp.") **Green.**
- **The auto-disconnect logic.** "The moment current flows in the circuit between the charger and the batteries the creature's own nervous system and motors are automatically disconnected; charging continues until the battery voltage has risen to its maximum. Then the internal circuits are automatically reconnected and the little creature, repelled now by the light which before the feast had been so irresistible, circles away for further adventures." (Walter 1950, p. 43 — verbatim.) **Green.**

### Behavioural modes (typology from Walter 1960 BNI typescript, named via Holland 2003)

- **E (exploration).** Driving motor on at half speed; steering / scanning motor on at full speed. Cycloidal trajectory through any environment without an attractive light. (Holland 2003, pp. 2100–2101, quoting Walter 1960 verbatim.) **Green.**
- **P (positive tropism).** Photocell aligned with a moderately bright source; first-stage current decreases slightly, second-stage current increases markedly, RL2 switches on. The turning motor receives no current; the drive motor receives full current. The tortoise heads toward the light. (Holland 2003, pp. 2101–2102.) **Green.**
- **N (negative tropism).** Photocell aligned with a strong light source; both stages saturate, RL1 switches state, the steering motor returns to full speed but inverted in effect. The tortoise sheers away from the light. (Walter 1950, p. 43 — verbatim "abruptly sheers away and seeks a more gentle climate"; Holland 2003 p. 2101 — circuit explanation.) **Green.**
- **O (obstacle-avoidance).** Shell-contact closes; the two-stage amplifier becomes a multivibrator; the relays oscillate, the motors oscillate, the photocell input is suppressed. "All stimuli are ignored and its gait is transformed into a succession of butts, withdrawals and sidesteps" (Walter 1950, p. 44, verbatim). After the obstacle is left behind, the oscillation persists for "about a second" — Walter's "short memory of frustration" — during which the tortoise gives the danger area a wide berth. (Walter 1950, p. 44; Holland 2003 pp. 2101–2102.) **Green.**

## The 1951 batch (improved build by W. J. "Bunny" Warren and the BNI engineering team)

- **Six improved tortoises** built in early 1951. Built specifically because Elmer and Elsie were "in consequence chronically unreliable" and could not be staked on demonstrations including the Festival of Britain. (Holland 2003, p. 2092 — verbatim.) **Green.**
- **Circuit identity.** "Almost identical" to the prototype design (Holland 2003, p. 2099 — the circuit diagram in Holland 2003's Figure 4 "describes the almost identical circuit used in the 1951 batch"). The improvements were in mechanical reliability and component sourcing, not in computational principle. **Green.**
- **Surviving tortoises.** Two of the six 1951 batch survive: one on display at the London Science Museum (since 2000), one at the MIT Museum (since 2001). (Holland 2003, p. 2092.) **Green.**
- **Disposition of Elmer and Elsie themselves.** Holland 2003 p. 2092: "Elmer and Elsie appear to have been scrapped at about this time" (i.e., early 1951). **Green** for the scrapping (with hedge "appear to have been"); **Yellow** for any precise disposition date.

## Von Neumann's worked example (1952)

- **Component count.** 2,500 vacuum tubes. (Von Neumann 1952, IAS PDF p. 45 — §10.5.3.1 verbatim.) **Green.**
- **Per-tube actuation rate.** Each tube actuated on the average once every 5 microseconds. (Same anchor.) **Green.**
- **Target reliability.** A mean free path of 8 hours between system errors. (Same anchor.) **Green.**
- **Total actuations per error-free interval.** "1.4 × 10¹³ actuations" — i.e., (1 / 5 microseconds) × 2,500 tubes × 8 hours × 3,600 seconds. (Same anchor.) **Green.**
- **Required error rate per actuation.** δ ≈ 1 / (1.4 × 10¹³) = 7 × 10⁻¹⁴. (Same anchor.) **Green.**
- **Required multiplexing factor.** N ≈ 14,000 (interpolating linearly on −10 log δ). (Same anchor.) **Green.**
- **Verdict on 1952 hardware.** "The multiplexing technique is impractical on the level of present technology, but quite practical for a perfectly conceivable more advanced technology and for the natural relay organs (neurons)." (Von Neumann 1952, IAS PDF p. 47 — §11.1 verbatim.) **Green.**

## What This Chapter Must NOT Claim About Infrastructure

- That Walter's tortoises were "purely analog." The amplifier was continuous; the behaviour states (E / P / N / O) were relay-mediated and discrete. The tortoises were a hybrid in their own design (Walter 1950, p. 42; Holland 2003, pp. 2100–2102). The chapter's framing must respect this hybridity.
- That von Neumann's 1952 lectures argued for "digital" over "analog." The lectures argue for *reliable* multiplexed systems built from *unreliable* basic components, where the basic components are explicitly modelled as digital binary elements (Sheffer-stroke organs and majority organs). The von Neumann argument applies to digital tube-based machines as much as to any analog scheme.
- That the cost or power consumption of the tortoise build limited it. No source in the citation bar gives a cost figure for Elmer / Elsie or for the 1951 batch. The Festival-of-Britain demand and the wartime-surplus component story (Holland 2003, p. 2092) anchor a *fragility* claim, not a cost claim.
- That a "city's power grid" or "skyscraper" would be required to scale Walter's design to brain complexity. This is the legacy chapter's prose colour and is not anchored in any verified source — neither Walter 1950 nor von Neumann 1952 makes this argument in those terms. The chapter may use the von Neumann 2,500-tube worked example with its actual figures (8-hour mean free path, N = 14,000), not invented power-grid analogies.

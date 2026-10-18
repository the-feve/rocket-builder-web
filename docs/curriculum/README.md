# Rockets and Model Rocketry: a 2-week home-school unit

_For about grades 3–8, in two tracks by age. Goes with **Rocket Builder by Quiver Design Works** (https://rocket.quiverdesignworks.net), a free web app for designing 3D-printable model rockets._

This unit teaches the science behind rockets: forces, motion, stability, drag, motors, parachutes and measuring height. Each day has a short lesson a parent can read aloud, one or two hands-on activities, a worksheet, discussion questions and a quick check. It ends with a launch day and a small project.

> **Model rocket motors and Rocket Builder kits are rated 12+.** Kids under 12 do the whole unit with paper-style rockets and use Rocket Builder on screen only. In the 12+ track, **adults handle all rocket motors and igniters**, every time, following the NAR Model Rocket Safety Code (see [Safety](#safety)).

## Pick a track by age

| | **Paper track: under 12** (about grades 3–6) | **Printed-rocket track: 12+** (about grades 7–8 and up) |
|---|---|---|
| Rockets you fly | Balloon, straw, paper and stomp rockets. Fizzy film-canister rockets only with an adult and safety glasses. | Everything in the paper track, **plus** a 3D-printed Rocket Builder rocket on a real model rocket motor on Day 10 |
| Rocket Builder | **On screen only:** design a rocket, read its stability score, and press **▶ Watch it launch** to see its simulated flight. No downloads, prints or orders. | Design it, download the files, print it (or order it printed), build it and fly it |
| Motors and igniters | None. Kids learn how motors work from pictures, the app and the worksheet. | Bought, stored, loaded and launched by an adult only. Kids design, build, check, count down and track. |
| Math | Whole numbers, simple decimals, averages, bar graphs, a multiplier table for angles | Adds ratios, F = m × a, impulse = average thrust × time, tangent, percent difference |
| Launch day | Stomp-rocket and fizzy-rocket launches with height tracking, parachute drops, and the app's simulated launch of their design. Optional: watch a local club launch as visitors. | An adult launches the printed rocket; the student tracks it and compares the flight with the app's prediction |
| Extra cost | About $40–60 | About $75–120 more, most of it reusable |

**Mixed ages?** Do the shared lessons together. Older kids add the 12+ steps and the grade 7–8 extensions; younger kids do the paper launches and the on-screen design. Everyone can track and record on launch day.

## Files

| File | What it is |
|---|---|
| `README.md` | This page: overview, tracks, schedule, materials, standards, safety |
| `day-01.md` … `day-10.md` | One lesson plan per day |
| `worksheets.html` | 22 printable pages for US Letter: worksheets W1–W9b, the inclinometer template, two launch logs (paper rockets; printed rocket 12+), the capstone planner and rubric, all ten quick checks, and answer keys at the end. Pages for the 12+ track are marked **12+**. Open it in a browser and print at 100% (turn on "background graphics" for the coloured headings). |
| `tools/gen_ws.py` | Builds `worksheets.html` (`python3 tools/gen_ws.py worksheets.html`) |
| `preview-w3-swing-test.png`, `preview-inclinometer.png` | Pictures of two worksheet pages |

## How each day works

Each day takes about **45–75 minutes** for younger kids and **60–90 minutes** for older ones. Every lesson has the same parts:

1. **Objectives**: what your student will be able to do.
2. **Vocabulary**: new words (they are also on the worksheet).
3. **Materials**: household things first, then anything to buy.
4. **Teach**: a short talk to read aloud or put in your own words (5–10 minutes).
5. **Activities**: one or two hands-on activities, step by step.
6. **Worksheet**: a page in `worksheets.html`.
7. **Discussion questions**.
8. **Quick check**: 3–5 short questions, with answers.
9. **Differentiation**: a simpler version for **younger kids (grades 3–6)**, and a **grade 7–8 extension** with more math.
10. **Track notes**: what's different in the **paper track (under 12)** and the **printed-rocket track (12+)**.

## Schedule at a glance

| Day | Big idea | Hands-on (everyone) | Paper track (under 12) | Printed-rocket track (12+) | Worksheet |
|---|---|---|---|---|---|
| 1 | What is a rocket? Newton's three laws | Balloon rocket on a string | First look at Rocket Builder on screen | Same, plus a grown-up **orders motors** and supplies | W1 Balloon rocket |
| 2 | The four forces | Paper straw rockets; launch-angle test | Watch the app's simulated launch: find boost, coast and parachute | Same; the app's power bar (thrust ÷ weight) | W2 Forces |
| 3 | Stability: balance point (CG) and push point (CP) | Balance point, cardboard cut-out, **string swing test** with a paper rocket | Find the blue and red dots in the app | Same; plan the swing test of the real rocket | W3 Swing test |
| 4 | Drag and shape | Nose-cone and fin tests with straw rockets | Compare nose shapes in the app | Same; change the drag number in Advanced | W4 Drag test |
| 5 | Motors, thrust and impulse | How a motor works (picture and app) | Fizzy film-canister rockets, **with an adult** | Same; motor codes, impulse math and the app's motor table | W5 Motors (W5b 12+) |
| 6 | The engineering design cycle | Rocket Builder design challenge: change one thing, record the score | Pick a favourite design and watch it launch on screen | Pick the final design and **start printing** | W6 Design log |
| 7 | Parachutes and descent rate | Parachute drop test | Make a parachute for a paper rocket | The app's parachute size; pack the real chute | W7 Drop test |
| 8 | Measuring height with angles | Make an inclinometer; measure a tree | Track a stomp rocket | Same; assemble the printed rocket | W8 Altitude + template |
| 9 | Safety, launch prep and graphing | Safety rules; countdown practice; graph your week | Paper-launch safety checklist | NAR code, misfire drill, preflight and swing test of the real rocket | W9, W9b |
| 10 | Launch day and mission report | Track, record, compare; capstone | Stomp and fizzy rocket launches; the app's launch of your design | An adult launches the printed rocket | Launch log, capstone |

### Short on time? A 1-week version

Do two days' worth each day. Keep the activity marked ★ in each lesson and skip or shorten the rest.

| Week day | Combine | Keep (paper track, under 12) | Add for 12+ |
|---|---|---|---|
| 1 | Days 1 + 2 | Balloon rocket ★, straw rockets ★ | Grown-up orders motors and supplies |
| 2 | Days 3 + 4 | Swing test ★, nose-cone test ★ | |
| 3 | Days 5 + 6 | Rocket Builder design challenge ★ (fizzy rockets optional, with an adult) | Motor codes page; start printing tonight |
| 4 | Days 7 + 8 | Parachute drop test ★, inclinometer ★ | Assemble the rocket |
| 5 | Days 9 + 10 | Safety rules ★, stomp-rocket launch day ★, a short spoken mission report | Preflight checks; the adult-run launch, or plan it for the weekend |

**12+ track in 1 week:** a print takes several hours, and a tall rocket is split into sections. Design the rocket on day 1 evening (Beginner mode and the defaults are fine), print on days 2–4, build on day 4. Or fly on the weekend after, or at a local club launch.

### Plan ahead (12+ track)

- **Day 1:** buy or order motors, a launch pad and controller, recovery wadding and a parachute (see the list below). Many hobby and craft stores sell model rocket motors; buying in a store avoids shipping fees for motors.
- **By Day 5:** find a launch field big enough for your motor (Days 5 and 9 explain field size). A local **NAR club launch** is a great option: they have the pads, a big field and experienced fliers. Find one at nar.org.
- **Day 6:** start printing. **Day 8:** assemble. **Day 10:** pick a backup day in case of wind or rain.

## Materials and costs by track

Most things are in your house already. Costs are rough 2026 US prices.

### Household (both tracks)

- Printer paper, cardstock or old cereal boxes, scrap cardboard, a paper-towel tube
- Clear tape, masking tape, glue stick, scissors, ruler, pencils
- Drinking straws, a few balloons (long ones work best)
- String or fishing line (5–10 m), paper clips, binder clips, a few metal washers
- Modeling clay or play dough
- Coffee filters, plastic grocery bags or trash bags, thread or dental floss
- Tape measure (10 m or more is best; a long string marked every metre also works)
- Stopwatch (a phone is fine), calculator
- Kitchen scale (optional; a 0.1 g scale is best)
- An empty plastic bottle (for a squeeze launcher)
- A computer or tablet for Rocket Builder

### Paper track (under 12): to buy

| Item | Used on | About |
|---|---|---|
| Safety glasses, one per person (kids' sizes exist) | Days 2, 4, 5, 8, 10 | $3–6 each |
| Protractor | Days 2, 8 | $1–3 |
| Film canisters with lids that snap *inside* the rim (10-pack) | Day 5 (adult-led) | $8–10 (sometimes free from photo shops) |
| Fizzy tablets: plain effervescent vitamin C tablets (or Alka-Seltzer, kept by the adult) | Day 5 | $5–8 |
| Stomp rocket kit, or DIY (2-litre bottle, 1 m of ½-inch PVC pipe, duct tape) | Days 8, 10 | $15–25 kit, $5–8 DIY |
| Kite string or fishing line, if you have none | Days 1, 3 | $3 |

**Paper-track total: about $40–60** (less if you have some already).

### Printed-rocket track (12+): add these

| Item | Notes | About |
|---|---|---|
| PLA filament | A small rocket uses roughly 50–100 g of a 1 kg spool | $1–3 per rocket ($18–22 a spool) |
| Launch pad and launch controller | Must have a safety key and a launch rod. Often sold as a set. A club launch provides these. | $35–50 |
| Batteries for the controller | | $4 |
| Model rocket motors (3-pack) | The size your design needs (M13, M18, M24 or M29), class picked in the app on Day 6. Many packs come with igniters. | $14–25 a pack |
| Recovery wadding (flame-resistant) | Protects the parachute from hot gas | $5 |
| Parachute (the size the app tells you, often 12–18 inches) | Plastic or nylon | $5–12 |
| Shock cord: braided flat elastic | Joins the nose to the body | $5–8 |
| Any glue, sandpaper or paint the build notes ask for | | $0–10 |

**12+ extra: about $75–120**, most of it reusable (the pad, controller and parachute). A rocket that survives can fly again with a new motor and wadding. No printer? Rocket Builder can order the rocket printed for you (a grown-up needs an account).

## Standards alignment

### NGSS, grades 3–5 (paper track)

| Standard | What it asks | Where |
|---|---|---|
| **3-PS2-1** | Investigate the effects of balanced and unbalanced forces on the motion of an object | Day 1 (balloon rocket), Day 2 (forces in each part of a flight), Day 7 (a parachute falling at a steady speed) |
| **3-PS2-2** | Observe and measure an object's motion to find a pattern that predicts future motion | Day 2 (launch angles), Day 7 (fall times), Day 8 (heights) |
| **5-PS2-1** | Argue that Earth's gravity pulls objects down | Day 2 (weight), Day 7 (parachutes) |
| **3-5-ETS1-1** | Define a simple design problem with criteria for success and constraints | Day 6 (score 1–2 cal, fits the field) |
| **3-5-ETS1-2** | Generate and compare several solutions against the criteria and constraints | Day 4 (noses and fins), Day 6 (design log and decision table) |
| **3-5-ETS1-3** | Plan and carry out fair tests in which variables are controlled and failure points are considered | Days 1, 3, 4, 7 |

### NGSS, middle school (both tracks; 12+ goes deeper)

| Standard | What it asks | Where |
|---|---|---|
| **MS-PS2-1** | Apply Newton's Third Law to design a solution to a problem involving the motion of two colliding objects | Day 1 (balloon rocket: action and reaction), Day 5 (fizzy rockets, motors), Day 10 |
| **MS-PS2-2** | Plan an investigation to provide evidence that the change in an object's motion depends on the sum of the forces on the object and the mass of the object | Day 1 (balloon + paper clips), Day 2 (forces), Day 5 (thrust-to-weight, F = ma) |
| **MS-ETS1-1** | Define the criteria and constraints of a design problem | Day 6 (score 1–2 cal, a ✓ motor, fits the printer and the field) |
| **MS-ETS1-2** | Evaluate competing design solutions using a systematic process | Day 4 (nose and fin tests), Day 6 (compare designs in a table) |
| **MS-ETS1-3** | Analyze data from tests to find the best characteristics of several designs | Days 3, 4, 6, 7 |
| **MS-ETS1-4** | Develop a model to generate data for iterative testing and modification | Day 6 (Rocket Builder is the model), Day 10 (prediction vs flight) |

Also touches MS-PS2-4 (gravity pulls everything down: weight) and MS-PS3-1 (faster means more kinetic energy) in the grade 7–8 extensions.

### Common Core math

| Standard | Where |
|---|---|
| 3.MD.B.3: scaled picture and bar graphs | Days 2, 4, 9 |
| 3.MD.B.4: measure lengths; show data on a line plot | Days 1, 2, 4 |
| 3.OA.C.7: multiply and divide within 100 | Day 5 (impulse), Day 7 (drift) |
| 4.MD.A.2: word problems with distances and time | Days 7, 8 |
| 4.MD.C.6: measure angles with a protractor | Day 2 (launch angles), Day 8 (inclinometer) |
| 5.NBT.B.7: add, subtract, multiply and divide decimals | Averages and rates, all week |
| 5.G.A.2: graph points in the first quadrant | Days 6, 7 |
| 6.RP.A.3: ratios and rates (unit rates, speed) | Days 5 (thrust-to-weight), 7 (descent rate in m/s), 9 (drift) |
| 6.EE.A.2: write and evaluate expressions from formulas | Days 3 (calibers), 5 (impulse), 7 (speed = distance ÷ time) |
| 6.SP.B.4, 6.SP.B.5: display data; mean and variability | Days 1, 2, 4, 7, 9 |
| 7.RP.A.2: proportional relationships | Days 5, 7, 8 |
| 7.G.B.5: angle relationships | Day 8 (the inclinometer) |
| 8.F.B.4, 8.SP.A.1: functions and scatter plots | Days 6, 7, 9 (grade 7–8 extensions) |
| HSG-SRT.C.8 (extension): use tangent to solve right triangles | Day 8, grade 7–8 extension |

### Common Core literacy in science

- RI.3.3 / RI.4.3 (younger): explain a procedure or the steps of a process (every activity; the flight of a rocket on Day 10).
- RST.6-8.3: follow a multistep procedure (every activity).
- RST.6-8.7: combine words with a diagram, graph or table (worksheets, launch logs).
- WHST.6-8.2: write to explain (the Day 10 mission report).

## Safety

Read this page before Day 1, and again before Day 10.

### The big rules

1. **Motors are 12+, and only adults handle them.** Model rocket motors and Rocket Builder kits are rated 12+. Kids under 12 don't fly motor rockets in this unit. In the 12+ track, an adult buys, stores and prepares every motor, puts in the igniter, puts the rocket on the pad, connects the clips, holds the safety key and presses the launch button. Kids can count down, and they design, build, check and track. Kids never carry the launch key.
2. **Glasses on** for straw, stomp and fizzy rockets, for everyone nearby.
3. **Never aim** any rocket at a person, animal or window.

### Paper-track safety (and for everyone during the week)

- **Straw and stomp rockets:** glasses on. Aim up or along an empty hallway, never at anyone. Wait until everyone is behind the launcher before stomping.
- **Fizzy film-canister rockets: adult-led only.** The adult keeps the tablets and hands out pieces. (Original Alka-Seltzer contains aspirin: it's medicine. Plain fizzy vitamin C tablets work too.) Outside only, glasses on, never lean over a canister. If one doesn't pop, wait at least 30 seconds, and the adult picks it up pointing away from faces.
- **Swing test:** outdoors, nobody within 3 m, short string (about 1 m).
- **Parachute drops** from a height: an adult does the dropping.
- **Inclinometer:** never look at the sun through the straw.

### Printed-rocket track (12+): the NAR Model Rocket Safety Code

This is a short, plain summary of the National Association of Rocketry's code. Younger kids learn the main rules too (Day 9), because they're good rules for any launch, and they'll need them if they visit a club launch. Read the official code at nar.org before launch day.

1. **Materials.** Rockets are made of light materials such as paper, wood, rubber and plastic. No metal for the nose, body or fins. (Printed PLA plastic is fine.)
2. **Motors.** Use only certified, store-bought model rocket motors, exactly as the maker says. Never change a motor or reload it. Store motors away from heat and flames.
3. **Ignition.** Launch with an electrical launch system and electric igniters. The controller has a **safety key**, and its button springs back to "off" when you let go.
4. **Misfires.** If the rocket doesn't launch when the button is pressed, take out the safety key (or disconnect the battery) and **wait 60 seconds** before anyone walks up to it.
5. **Launch safety.** Count down out loud from 5 so everyone knows. Everyone pays attention and stands **at least 15 feet (about 5 m) away** for D motors or smaller, and 30 feet for bigger ones. Check the rocket is stable before its first flight.
6. **Launcher.** Use a launch rod or rail pointed within 30 degrees of straight up, with a blast deflector. Clear dry grass and anything that burns from around the pad. Keep the top of the rod above eye level or cover it when not in use.
7. **Size.** A model rocket weighs no more than 1,500 g at liftoff. (All the rockets in this unit are far smaller.)
8. **Flight safety.** Never launch at targets, into clouds, near airplanes or over people.
9. **Launch site.** Outdoors, in a large open area away from tall trees, power lines and buildings. **Not in winds over 20 mph.** The field must be at least as big as the table below.
10. **Recovery.** Use a parachute or streamer so the rocket comes down gently and can fly again. Use only flame-resistant wadding.
11. **Recovery safety.** Never try to get a rocket out of a power line, a tall tree or another dangerous place. Never try to catch a rocket as it comes down.

**Minimum field size (from the NAR code; also used by Rocket Builder):**

| Motor class | Total impulse (N·s) | Smallest field side |
|---|---|---|
| 1/4A, 1/2A | up to 1.25 | 50 ft (15 m) |
| A | 1.26–2.5 | 100 ft (30 m) |
| B | 2.51–5 | 200 ft (60 m) |
| C | 5.01–10 | 400 ft (120 m) |
| D | 10.01–20 | 500 ft (150 m) |
| E, F | 20.01–80 | 1,000 ft (300 m) |

This is the **smallest** field. A rocket also drifts sideways in the wind under its parachute, so Rocket Builder often suggests a longer field. Day 9 shows how to work that out.

Also check: local rules (some towns, parks and states have their own), fire danger (don't launch when the grass is dry and there's a burn ban), and stay well away from airports.

Also for the 12+ track:

- **3D printer:** the nozzle and bed are hot. A grown-up runs the printer, in a room with fresh air.
- **Launch day:** follow the [launch day rules](day-10.md#launch-day-rules).

## A note on the numbers

The numbers here match Rocket Builder: stability in calibers (1–2 cal is ideal, under 1 is too wobbly to download, over 3 is too stable); thrust at least **5 times** the weight; at least **15 m/s** off the launch rod; at least **30 m** high so the parachute can open; and a parachute that brings the rocket down at about **3–5 m/s**. The app's numbers are quick estimates. Real flights differ a bit, which is part of the fun on Day 10: compare the prediction with what really happened.

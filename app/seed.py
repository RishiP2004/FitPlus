"""Preset exercise library (PB-09). Seeding is idempotent: existing names are skipped."""
from .db import execute, query_all

# (name, muscle group, equipment, instructions)
PRESET_EXERCISES = [
    # Chest
    ("Barbell Bench Press", "Chest", "Barbell",
     "Lie on a flat bench with eyes under the bar. Grip slightly wider than shoulders, lower the bar to mid-chest with elbows about 45 degrees, then press up until arms are straight."),
    ("Incline Dumbbell Press", "Chest", "Dumbbell",
     "Set a bench to 30-45 degrees. Start with dumbbells at chest level, press them up and slightly together, then lower under control to the sides of the chest."),
    ("Dumbbell Flyes", "Chest", "Dumbbell",
     "Lie on a flat bench holding dumbbells above the chest with a slight bend in the elbows. Open the arms wide in an arc until you feel a stretch, then squeeze them back together."),
    ("Push-Up", "Chest", "Bodyweight",
     "Start in a plank with hands just wider than shoulders. Keep a straight line from head to heels, lower the chest to just above the floor, then push back up."),
    ("Cable Crossover", "Chest", "Cable",
     "Set both pulleys high. Step forward with a handle in each hand, then bring the hands down and together in front of the hips. Return slowly with control."),
    ("Chest Press Machine", "Chest", "Machine",
     "Adjust the seat so handles are at mid-chest. Press the handles forward until arms are extended without locking, then return slowly."),
    ("Dips (Chest)", "Chest", "Bodyweight",
     "On parallel bars, lean the torso forward slightly. Lower until the upper arms are about parallel to the floor, then push back up."),
    # Back
    ("Deadlift", "Back", "Barbell",
     "Stand with mid-foot under the bar. Hinge to grip it, brace the core, keep a flat back and drive through the floor to stand tall. Lower by pushing the hips back."),
    ("Pull-Up", "Back", "Bodyweight",
     "Hang from a bar with an overhand grip slightly wider than shoulders. Pull until the chin clears the bar, then lower to a full hang."),
    ("Lat Pulldown", "Back", "Cable",
     "Sit with thighs under the pads. Grip the bar wide, pull it to the upper chest while leaning back slightly, then let it rise slowly."),
    ("Bent-Over Barbell Row", "Back", "Barbell",
     "Hinge forward to about 45 degrees with a flat back. Pull the bar to the lower ribs, squeeze the shoulder blades, then lower with control."),
    ("Single-Arm Dumbbell Row", "Back", "Dumbbell",
     "Place one knee and hand on a bench. Row the dumbbell toward the hip, keeping the elbow close, then lower it fully."),
    ("Seated Cable Row", "Back", "Cable",
     "Sit tall with feet on the platform. Pull the handle to the stomach, squeeze the shoulder blades together, then extend the arms slowly."),
    ("Resistance Band Pull-Apart", "Back", "Resistance Band",
     "Hold a band at shoulder height with straight arms. Pull it apart until it touches the chest, squeezing the upper back, then return slowly."),
    # Shoulders
    ("Overhead Press", "Shoulders", "Barbell",
     "Stand with the bar at the front of the shoulders. Brace the core and press the bar straight overhead, moving the head back slightly, then lower to the shoulders."),
    ("Seated Dumbbell Shoulder Press", "Shoulders", "Dumbbell",
     "Sit on an upright bench with dumbbells at shoulder height. Press them overhead until arms are straight, then lower to ear level."),
    ("Lateral Raise", "Shoulders", "Dumbbell",
     "Stand holding dumbbells at your sides. Raise the arms out to shoulder height with a slight elbow bend, then lower slowly."),
    ("Front Raise", "Shoulders", "Dumbbell",
     "Hold dumbbells in front of the thighs. Raise one or both arms straight forward to shoulder height, then lower slowly."),
    ("Face Pull", "Shoulders", "Cable",
     "Set a rope at upper-chest height. Pull the rope toward the face, separating the ends and pointing elbows out, then return slowly."),
    ("Reverse Pec Deck", "Shoulders", "Machine",
     "Sit facing the machine pad. Hold the handles with arms straight in front, then open the arms out and back, squeezing the rear shoulders."),
    # Biceps
    ("Barbell Curl", "Biceps", "Barbell",
     "Stand holding a bar with an underhand grip. Keep elbows at your sides and curl the bar to the shoulders, then lower fully."),
    ("Dumbbell Hammer Curl", "Biceps", "Dumbbell",
     "Hold dumbbells with palms facing each other. Curl them toward the shoulders without swinging, then lower slowly."),
    ("Incline Dumbbell Curl", "Biceps", "Dumbbell",
     "Sit back on an incline bench with arms hanging. Curl the dumbbells up while keeping the upper arms still, then lower fully."),
    ("Cable Curl", "Biceps", "Cable",
     "Stand facing a low pulley with a straight bar. Curl the bar toward the chest, keeping the elbows fixed, then lower slowly."),
    ("Resistance Band Curl", "Biceps", "Resistance Band",
     "Stand on the band and hold the handles. Curl the hands to the shoulders, then lower with control."),
    # Triceps
    ("Triceps Pushdown", "Triceps", "Cable",
     "Face a high pulley holding a bar or rope. Keep elbows at your sides and push down until the arms are straight, then let it rise slowly."),
    ("Overhead Dumbbell Triceps Extension", "Triceps", "Dumbbell",
     "Hold one dumbbell overhead with both hands. Lower it behind the head by bending the elbows, then extend back up."),
    ("Skull Crusher", "Triceps", "Barbell",
     "Lie on a bench with an EZ or straight bar above the chest. Bend the elbows to lower the bar toward the forehead, then extend the arms."),
    ("Bench Dips", "Triceps", "Bodyweight",
     "Place hands on a bench behind you with legs out front. Lower the hips by bending the elbows to about 90 degrees, then push back up."),
    ("Close-Grip Bench Press", "Triceps", "Barbell",
     "Lie on a flat bench and grip the bar about shoulder-width. Lower to the lower chest with elbows tucked, then press up."),
    # Quadriceps
    ("Barbell Back Squat", "Quadriceps", "Barbell",
     "Rest the bar on the upper back, feet shoulder-width. Sit down and back until thighs are at least parallel, keep the chest up, then drive up."),
    ("Goblet Squat", "Quadriceps", "Dumbbell",
     "Hold a dumbbell or kettlebell at the chest. Squat down between the knees with an upright torso, then stand up."),
    ("Leg Press", "Quadriceps", "Machine",
     "Sit with feet shoulder-width on the platform. Lower the platform until knees are about 90 degrees, then press back without locking the knees."),
    ("Walking Lunge", "Quadriceps", "Dumbbell",
     "Hold dumbbells at your sides. Step forward and lower until both knees are about 90 degrees, then step through into the next lunge."),
    ("Leg Extension", "Quadriceps", "Machine",
     "Sit with the pad on the lower shins. Straighten the legs fully, squeeze the thighs, then lower slowly."),
    ("Bulgarian Split Squat", "Quadriceps", "Dumbbell",
     "Rest the back foot on a bench. Lower the back knee toward the floor, keeping the front knee over the foot, then drive up through the front heel."),
    ("Bodyweight Squat", "Quadriceps", "Bodyweight",
     "Stand with feet shoulder-width. Sit the hips back and down to a comfortable depth, keeping heels down, then stand up."),
    # Hamstrings
    ("Romanian Deadlift", "Hamstrings", "Barbell",
     "Hold the bar at hip height. Push the hips back with a slight knee bend, lowering the bar along the legs until you feel a hamstring stretch, then return."),
    ("Lying Leg Curl", "Hamstrings", "Machine",
     "Lie face down with the pad above the heels. Curl the heels toward the glutes, then lower slowly."),
    ("Kettlebell Swing", "Hamstrings", "Kettlebell",
     "Hinge to hike the kettlebell between the legs, then drive the hips forward to swing it to chest height. Let it fall back into the next hinge."),
    ("Single-Leg Dumbbell RDL", "Hamstrings", "Dumbbell",
     "Hold a dumbbell and stand on one leg. Hinge forward while the free leg extends behind, keep the back flat, then return to standing."),
    # Glutes
    ("Barbell Hip Thrust", "Glutes", "Barbell",
     "Sit with upper back on a bench and the bar over the hips. Drive the hips up until the body is flat from shoulders to knees, squeeze, then lower."),
    ("Glute Bridge", "Glutes", "Bodyweight",
     "Lie on your back with knees bent. Push through the heels to lift the hips until the body is straight from shoulders to knees, then lower."),
    ("Cable Kickback", "Glutes", "Cable",
     "Attach an ankle strap to a low pulley. Kick the leg straight back, squeezing the glute, then return slowly."),
    ("Banded Lateral Walk", "Glutes", "Resistance Band",
     "Place a band above the knees and bend slightly. Step sideways keeping tension on the band for 10-15 steps, then switch direction."),
    # Calves
    ("Standing Calf Raise", "Calves", "Machine",
     "Stand with the balls of the feet on the platform. Rise onto the toes as high as possible, pause, then lower the heels below the platform."),
    ("Seated Calf Raise", "Calves", "Machine",
     "Sit with the pad on the lower thighs. Raise the heels as high as possible, pause, then lower slowly."),
    ("Single-Leg Calf Raise", "Calves", "Bodyweight",
     "Stand on one foot on a step. Rise onto the toes, pause, then lower the heel below the step."),
    # Core
    ("Plank", "Core", "Bodyweight",
     "Hold a push-up position on the forearms with the body straight from head to heels. Brace the core and breathe steadily for the set time."),
    ("Crunch", "Core", "Bodyweight",
     "Lie on your back with knees bent. Curl the shoulders off the floor toward the hips, then lower slowly."),
    ("Hanging Leg Raise", "Core", "Bodyweight",
     "Hang from a bar. Raise the legs to hip height or higher without swinging, then lower slowly."),
    ("Russian Twist", "Core", "Bodyweight",
     "Sit with knees bent and lean back slightly. Rotate the torso side to side, touching the floor beside each hip."),
    ("Cable Woodchopper", "Core", "Cable",
     "Set a pulley high. Pull the handle diagonally across the body to the opposite hip, rotating through the torso, then return slowly."),
    ("Ab Wheel Rollout", "Core", "Bodyweight",
     "Kneel holding an ab wheel. Roll forward as far as you can while keeping the back flat, then pull back to the start."),
    # Full Body
    ("Burpee", "Full Body", "Bodyweight",
     "From standing, squat and place hands down, jump the feet back to a plank, return the feet, then jump up with arms overhead."),
    ("Kettlebell Clean and Press", "Full Body", "Kettlebell",
     "Swing the kettlebell up into the rack position at the shoulder, then press it overhead. Lower to the rack, then back between the legs."),
    ("Mountain Climber", "Full Body", "Bodyweight",
     "Start in a plank. Drive one knee toward the chest, then switch legs quickly, keeping the hips level."),
    ("Dumbbell Thruster", "Full Body", "Dumbbell",
     "Hold dumbbells at the shoulders. Squat down, then drive up and press the dumbbells overhead in one movement."),
]


def seed_exercises():
    existing = {
        r["name"] for r in query_all("SELECT name FROM exercises WHERE created_by IS NULL")
    }
    added = 0
    for name, muscle, equipment, instructions in PRESET_EXERCISES:
        if name in existing:
            continue
        execute(
            "INSERT INTO exercises (name, muscle_group, equipment, instructions, is_preset) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, muscle, equipment, instructions, True),
        )
        added += 1
    return added

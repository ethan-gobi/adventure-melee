// Sonic fighter code (m-ex). Four specials as Sonic's own action states.
//   Neutral B  Homing Attack     (state 341)  air dash that steers at the nearest opponent; bounces off on hit
//   Side B     Spin Dash         (342 charge, 343 roll)  hold B to rev, release to roll
//   Up B       Light Speed Dash  (344)  fast straight dash in the stick direction, then helpless fall
//   Down B     Bounce Attack     (345)  plunge as a ball, rebound off the floor
// All numbers here are designed for this mod.
#include "../tools/m-ex/MexTK/include/mex.h"

#define ST_HOMING 341
#define ST_CHARGE 342
#define ST_ROLL 343
#define ST_LSD 344
#define ST_BOUNCE 345
#define ST_LD_CHARGE_G 347 // Light Dash (side B, after SSF2): ground pause
#define ST_LD_CHARGE_A 348 // air pause
#define ST_LD_GROUND 349   // dash along the floor
#define ST_LD_AIR 350      // dash in the air (also the diagonal dashes)
#define LD_PAUSE 18
#define LD_SPEED 3.9f
#define LD_FRAMES 12
#define LD_END 30
#define ST_TAILS 351 // v69: air up B, Tails carries Sonic up (anim SpecialHiCatch, 309)
#define TAILS_FRAMES 70   // carried this long, then Tails lets go: helpless fall (v70: 60 -> 70)
#define TAILS_RISE 1.15f  // rising speed for frames 8-45, then it fades to 0.35 by the end (v70: 1.0 -> 1.15, 40 -> 45, 0.2 -> 0.35)
#define TAILS_PIVOT_Y 20.49f // Tails model origin on bone 62 (model builder, PlSnNr_v69_tails.json)
#define TAILS_PIVOT_Z -2.99f
#define TAILS_FLYOFF 30    // v75: frames Tails takes to fly up and away, shrinking, after letting go
#define TAILS_WINDOW 30    // v75: frames Sonic can still act after a natural release before free fall
#define TAILS_DRIFT 1.1f  // max sideways speed, steered with the stick (v70: 0.9 -> 1.1)
#define ST_LSD_SIDE 346 // same move as 344 with the head-first flying pose, used when the dash is mostly sideways

#define HOMING_RANGE 75.0f
#define HOMING_SPEED 3.4f
#define HOMING_FRAMES 24
#define HOMING_TRACK 6 // v70: frames the dash keeps steering at the target
#define AIRDASH_SPEED 2.8f
#define AIRDASH_FRAMES 12
#define HOMING_ENDLAG 52 // extra frames after the dash where Sonic just falls and cannot act (v52: 14 -> 24, v54: -> 32, v58: -> 44, v61: -> 60, v70: -> 52 (user: less);
                         // before v58 the 40-frame animation ended the move early, so only about 16 frames ever played)
#define HOMING_HITLAG 30 // frames after a hit, popping up and back, before he can act (v52: 0 -> 12, v54: -> 20, v58: -> 26, v61: -> 34, v70: -> 30)
#define HOMING_LANDLAG 24.0f // landing lag if he touches the floor during the move (v54: 4 -> 14, v58: -> 20, v61: -> 28, v70: -> 24)
#define HOMING_HIT_LANDLAG 20.0f // landing lag if he touches the floor during the pop-up after a hit (v58-v60 value, kept in v61)
#define HOMING_LANDLAG_MAX 40.0f // v59: a missed Homing Attack that lands takes its remaining end lag as landing lag, up to this (v61: 36 -> 48, v70: -> 40)
#define BOUNCE_ENDLAG 18 // frames after the rebound before Sonic can act
#define ROLL_BASE 3.0f
#define ROLL_BONUS 1.6f
#define CHARGE_MAX 45
#define CHARGE_HOLD_MAX 180 // the rev can be held this long before it releases by itself (v54: 60 -> 180)
#define DOWNB_JUMP_FRAMES 120 // two seconds after down B starts (rev + roll), jump cancels it (v54)
#define ROLL_FRAMES 34
#define LSD_SPEED 3.3f
#define LSD_FRAMES 12
#define LSD_START 8 // Peel-Out rev: frames hovering in place before the launch (v54)
#define LSD_END 30
#define BOUNCE_HOP 2.4f
#define BOUNCE_ACCEL 0.45f
#define BOUNCE_MAX -4.6f
#define BOUNCE_REBOUND 3.0f
#define BOUNCE_REBOUND_STEP 0.45f // v64: each bounce in a row without landing rebounds higher (SA2 Bounce Bracelet): 3.0, 3.45, 3.9
#define BOUNCE_REBOUND_STEPS 2
#define BLINK_PERIOD 170 // v64: frames between blinks
#define BLINK_LEN 5

#define INL static inline __attribute__((always_inline))
typedef union { int i; float f; } IF; // to keep a float in an int state variable

INL float SqrtN(float x)
{
    if (!(x > 0.0f))
        return 0.0f;
    float g = (x > 1.0f) ? x * 0.5f : 1.0f;
    for (int i = 0; i < 14; i++)
        g = 0.5f * (g + x / g);
    return g;
}

// nearest other fighter within range; writes the offset from Sonic's centre to the target's centre
INL int FindTarget(GOBJ *fighter, float *dx, float *dy)
{
    FighterData *fd = fighter->userdata;
    int found = 0;
    float best = HOMING_RANGE * HOMING_RANGE;
    for (int i = 0; i < 6; i++)
    {
        GOBJ *g = Fighter_GetGObj(i);
        if (g == 0 || g == fighter)
            continue;
        FighterData *od = g->userdata;
        if (od == 0)
            continue;
        float x = od->phys.pos.X - fd->phys.pos.X;
        float y = (od->phys.pos.Y + 6.0f) - (fd->phys.pos.Y + 5.0f);
        float d2 = x * x + y * y;
        if (d2 < best)
        {
            best = d2;
            found = 1;
            *dx = x;
            *dy = y;
        }
    }
    return found;
}

void Sonic_OnHit(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var3 = 1;
}

INL void EnterState(GOBJ *fighter, int state)
{
    FighterData *fd = fighter->userdata;
    ActionStateChange(0, 1, 0, fighter, state, 0, 0);
    Fighter_AdvanceScript(fighter);
    fd->state_var.state_var1 = 0; // frame counter
    fd->state_var.state_var2 = 0;
    fd->state_var.state_var3 = 0; // set by Sonic_OnHit
    fd->state_var.state_var4 = 0;
    fd->cb.OnGiveDamage = Sonic_OnHit;
}

// ---------------------------------------------------------------- Homing Attack
INL void HomingStart(GOBJ *fighter, int allow_target)
{
    FighterData *fd = fighter->userdata;
    if (fd->phys.air_state == 0)
        Fighter_SetAirborne(fd);
    else if (fd->fighter_var.ft_var5)
        return; // already missed one this airtime (v70: own flag, so a miss no longer uses up the double jump); cleared on landing / ledge
    float dx = 0, dy = 0;
    int has = allow_target ? FindTarget(fighter, &dx, &dy) : 0;
    if (has && dx != 0.0f)
        fd->facing_direction = (dx > 0.0f) ? 1.0f : -1.0f;
    fd->phys.self_vel.X = AIRDASH_SPEED * fd->facing_direction;
    fd->phys.self_vel.Y = 0.5f;
    EnterState(fighter, ST_HOMING);
    fd->state_var.state_var2 = has;
}

void SpecialN(GOBJ *fighter) { HomingStart(fighter, 1); }
void SpecialAirN(GOBJ *fighter) { HomingStart(fighter, 1); }

void Homing_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var3 && fd->state_var.state_var4 == 0)
    { // hit something: pop up and back
        fd->phys.self_vel.X = -0.6f * fd->facing_direction;
        fd->phys.self_vel.Y = 2.4f;
        fd->state_var.state_var4 = 1;
        return;
    }
    if (fd->state_var.state_var4 > 0)
    { // end lag after a hit
        fd->state_var.state_var4++;
        if (fd->state_var.state_var4 > HOMING_HITLAG)
            Fighter_EnterFall(fighter);
        return;
    }
    int limit = (fd->state_var.state_var2 ? HOMING_FRAMES : AIRDASH_FRAMES) + HOMING_ENDLAG;
    if (fd->state_var.state_var1 > limit || FrameTimerCheck(fighter) == 0)
    { // missed: normal fall (not helpless), but no second Homing Attack or double jump until landing
        fd->fighter_var.ft_var5 = 1;
        Fighter_EnterFall(fighter);
    }
}

void Homing_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var4 > 0)
    { // popping up after a hit
        fd->phys.self_vel.X = fd->phys.self_vel.X * 0.95f;
        fd->phys.self_vel.Y = fd->phys.self_vel.Y - 0.15f;
        return;
    }
    if (fd->state_var.state_var1 > (fd->state_var.state_var2 ? HOMING_FRAMES : AIRDASH_FRAMES))
    { // end lag (v70): he can drift with the stick and falls slower, so a miss off stage can still recover
        float vx = fd->phys.self_vel.X * 0.9f + fd->input.lstick.X * 0.06f;
        if (vx > 1.0f)
            vx = 1.0f;
        if (vx < -1.0f)
            vx = -1.0f;
        fd->phys.self_vel.X = vx;
        float vy = fd->phys.self_vel.Y - 0.10f;
        fd->phys.self_vel.Y = (vy < -1.8f) ? -1.8f : vy;
        return;
    }
    if (fd->state_var.state_var2 && fd->state_var.state_var1 <= HOMING_TRACK)
    { // v70: steers only for the first HOMING_TRACK frames, then flies straight (it used to chase an air-dodging target)
        float dx = 0, dy = 0;
        if (FindTarget(fighter, &dx, &dy))
        {
            float len = SqrtN(dx * dx + dy * dy);
            if (len > 1.5f && len < 400.0f)
            {
                fd->phys.self_vel.X = HOMING_SPEED * dx / len;
                fd->phys.self_vel.Y = HOMING_SPEED * dy / len;
            }
        }
    }
    else
    {
        fd->phys.self_vel.Y = fd->phys.self_vel.Y - 0.03f;
    }
}

void Air_Coll(GOBJ *fighter)
{
    Fighter_CollAir_IgnoreLedge(fighter, Fighter_EnterLanding);
}

void Homing_Land(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    float lag = HOMING_HIT_LANDLAG;
    if (fd->state_var.state_var4 == 0)
    { // v59: a miss that lands spends the rest of its end lag as landing lag (v54-v58 it skipped the end lag entirely)
        int limit = (fd->state_var.state_var2 ? HOMING_FRAMES : AIRDASH_FRAMES) + HOMING_ENDLAG;
        float left = (float)(limit - fd->state_var.state_var1);
        lag = HOMING_LANDLAG;
        if (left > lag)
            lag = left;
        if (lag > HOMING_LANDLAG_MAX)
            lag = HOMING_LANDLAG_MAX;
    }
    Fighter_EnterSpecialLanding(fighter, 0, lag);
}

void Homing_Coll(GOBJ *fighter)
{
    Fighter_CollAir_IgnoreLedge(fighter, Homing_Land);
}

// ---------------------------------------------------------------- Spin Dash
void SpecialS(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->phys.self_vel_ground.X = 0;
    EnterState(fighter, ST_LD_CHARGE_G);
}

void SpecialAirS(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->phys.self_vel.X = 0;
    fd->phys.self_vel.Y = 0;
    EnterState(fighter, ST_LD_CHARGE_A);
}

// pause, then launch: straight, or diagonally up/down if the stick is held that way as the dash begins
void LdCharge_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 < LD_PAUSE)
        return;
    float sy = fd->input.lstick.Y;
    int grounded = (fd->phys.air_state == 0);
    if (grounded && sy < 0.4f)
    { // along the floor (down-diagonal is not possible from the ground)
        EnterState(fighter, ST_LD_GROUND);
        fd->phys.self_vel_ground.X = LD_SPEED * fd->facing_direction;
        return;
    }
    if (grounded)
        Fighter_SetAirborne(fd);
    float vx = LD_SPEED, vy = 0.0f;
    if (sy >= 0.4f)
    {
        vx = LD_SPEED * 0.866f;
        vy = LD_SPEED * 0.5f;
    }
    else if (sy <= -0.4f)
    {
        vx = LD_SPEED * 0.866f;
        vy = -LD_SPEED * 0.5f;
    }
    EnterState(fighter, ST_LD_AIR);
    fd->phys.self_vel.X = vx * fd->facing_direction;
    fd->phys.self_vel.Y = vy;
}

void LdChargeAir_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->phys.self_vel.X = 0;
    fd->phys.self_vel.Y = 0;
}

void LdGround_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 > LD_END || FrameTimerCheck(fighter) == 0)
        Fighter_EnterWait(fighter);
}

void LdGround_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var1 > LD_FRAMES)
        fd->phys.self_vel_ground.X = fd->phys.self_vel_ground.X * 0.8f; // skid to a stop
    Fighter_PhysGround_ApplyVelocity(fighter);
}

void LdAir_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 > LD_FRAMES + 6 || FrameTimerCheck(fighter) == 0)
        Fighter_EnterSpecialFall(fighter, 1, 1, 0, 1.0f, 15.0f); // helpless until he lands, as in SSF2
}

void LdAir_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var1 > LD_FRAMES)
    {
        fd->phys.self_vel.X = fd->phys.self_vel.X * 0.8f;
        fd->phys.self_vel.Y = fd->phys.self_vel.Y * 0.8f - 0.1f;
    }
}

// Spin Dash (now ground down B, as in SSF2): hold B to rev, release to roll
void Charge_IASA(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    int t = fd->state_var.state_var1;
    if (t >= DOWNB_JUMP_FRAMES && Fighter_IASACheck_JumpF(fighter))
        return; // jumped out of the rev
    if (t >= 8 && (!(fd->input.held & PAD_BUTTON_B) || t >= CHARGE_HOLD_MAX))
    {
        int c = (t > CHARGE_MAX) ? CHARGE_MAX : t;
        float speed = ROLL_BASE + ROLL_BONUS * (float)c / (float)CHARGE_MAX;
        EnterState(fighter, ST_ROLL);
        fd->state_var.state_var5 = t; // frames already spent revving, for the two-second jump cancel
        fd->phys.self_vel_ground.X = speed * fd->facing_direction;
    }
}

void Roll_IASA(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var5 + fd->state_var.state_var1 >= DOWNB_JUMP_FRAMES)
        Fighter_IASACheck_JumpF(fighter);
}

void Ground_Phys(GOBJ *fighter)
{
    Fighter_PhysGround_ApplyFriction(fighter);
}

void Ground_Coll(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (Fighter_CollGround_PassLedge(fighter) == 0)
    {
        Fighter_SetAirborne(fd);
        Fighter_EnterFall(fighter);
    }
}

void Roll_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 > ROLL_FRAMES || FrameTimerCheck(fighter) == 0)
        Fighter_EnterWait(fighter);
}

void Roll_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->phys.self_vel_ground.X = fd->phys.self_vel_ground.X * 0.97f;
    Fighter_PhysGround_ApplyVelocity(fighter);
}

// ---------------------------------------------------------------- Light Speed Dash
// Up B: Super Peel-Out. Rev in place for LSD_START frames, then launch in the direction the stick is held AT THAT MOMENT
// (straight up-forward if it is neutral), like aiming Fox's up B. Mostly-sideways launches switch to the leaning pose (state 346).
INL void LsdStart(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->phys.air_state == 0)
        Fighter_SetAirborne(fd);
    fd->phys.self_vel.X = 0;
    fd->phys.self_vel.Y = 0.12f; // rev phase: hover, drifting up very slightly so he does not land
    EnterState(fighter, ST_LSD);
}

void SpecialHi(GOBJ *fighter) { LsdStart(fighter); }
void SpecialAirHi(GOBJ *fighter)
{ // v69: Tails carry (Sonic 3). Ground up B is still the Peel-Out.
    FighterData *fd = fighter->userdata;
    if (fd->fighter_var.ft_var4)
        return; // already cancelled one carry this airtime (cleared on landing in OnFrame)
    EnterState(fighter, ST_TAILS);
    fd->phys.self_vel.X = fd->phys.self_vel.X * 0.5f;
    fd->phys.self_vel.Y = 0.0f;
}

void Tails_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 > 8 && (fd->input.held & (PAD_TRIGGER_L | PAD_TRIGGER_R)))
    { // v70: shield cancels the carry: Tails lets go, normal fall (can air dodge), no second up B until he lands
        fd->fighter_var.ft_var4 = 1;
        fd->fighter_var.ft_var6 = 1; // Tails flies off
        fd->jump.jumps_used = fd->attr.max_jumps; // v75: no jump after up B (user), cancelled or not
        Fighter_EnterFall(fighter);
        return;
    }
    if (fd->state_var.state_var1 > TAILS_FRAMES)
    { // v75: Tails lets go and flies off; Sonic can act for TAILS_WINDOW frames (no double jump, no second carry), then free fall
        fd->fighter_var.ft_var4 = 1;
        fd->fighter_var.ft_var6 = 1;
        fd->fighter_var.ft_var7 = 1;
        fd->jump.jumps_used = fd->attr.max_jumps;
        Fighter_EnterFall(fighter);
    }
}

void Tails_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    int t = fd->state_var.state_var1;
    float vy;
    if (t < 8)
        vy = 0.0f; // Tails swoops in and grabs his hands
    else if (t < 45)
        vy = TAILS_RISE;
    else
        vy = TAILS_RISE - (TAILS_RISE - 0.35f) * (float)(t - 45) / (float)(TAILS_FRAMES - 45);
    fd->phys.self_vel.Y = vy;
    float vx = fd->phys.self_vel.X * 0.96f + fd->input.lstick.X * 0.10f;
    if (vx > TAILS_DRIFT)
        vx = TAILS_DRIFT;
    if (vx < -TAILS_DRIFT)
        vx = -TAILS_DRIFT;
    fd->phys.self_vel.X = vx;
}

void Lsd_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 == LSD_START)
    { // launch
        float sx = fd->input.lstick.X, sy = fd->input.lstick.Y;
        float len = SqrtN(sx * sx + sy * sy);
        if (len < 0.35f)
        { // no direction held: up and slightly forward
            sx = 0.3f * fd->facing_direction;
            sy = 1.0f;
            len = SqrtN(sx * sx + sy * sy);
        }
        if (sx > 0.2f)
            fd->facing_direction = 1.0f;
        if (sx < -0.2f)
            fd->facing_direction = -1.0f;
        float ax = sx < 0.0f ? -sx : sx, ay = sy < 0.0f ? -sy : sy;
        if (ax > ay * 1.2f && fd->state_id == ST_LSD)
        { // mostly sideways: same move, leaning pose, picked up at the launch frame
            ActionStateChange((float)LSD_START, 1, 0, fighter, ST_LSD_SIDE, 0, 0);
            Fighter_AdvanceScript(fighter);
            fd->state_var.state_var1 = LSD_START;
            fd->state_var.state_var3 = 0;
            fd->cb.OnGiveDamage = Sonic_OnHit;
        }
        fd->phys.self_vel.X = LSD_SPEED * sx / len;
        fd->phys.self_vel.Y = LSD_SPEED * sy / len;
        return;
    }
    if (fd->state_var.state_var1 > LSD_END || FrameTimerCheck(fighter) == 0)
        Fighter_EnterSpecialFall(fighter, 1, 1, 0, 1.0f, 15.0f);
}

void Lsd_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    int t = fd->state_var.state_var1;
    if (t < LSD_START)
    { // Peel-Out rev: stay put
        fd->phys.self_vel.X = 0;
        fd->phys.self_vel.Y = 0.12f;
        return;
    }
    if (t > LSD_START + LSD_FRAMES)
    {
        fd->phys.self_vel.X = fd->phys.self_vel.X * 0.85f;
        fd->phys.self_vel.Y = fd->phys.self_vel.Y * 0.85f - 0.08f;
    }
}

void Lsd_Coll(GOBJ *fighter)
{
    Fighter_CollAir_GrabBothLedgesWalljump(fighter, Fighter_EnterLanding);
}

// ---------------------------------------------------------------- Bounce Attack
void SpecialLw(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->phys.self_vel_ground.X = 0;
    EnterState(fighter, ST_CHARGE);
}

void SpecialAirLw(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->phys.self_vel.Y > 0.0f)
        fd->phys.self_vel.Y = 0.0f;
    EnterState(fighter, ST_BOUNCE);
}

void Bounce_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var2 > 0)
    { // rebounding: end lag before he can act
        fd->state_var.state_var2++;
        if (fd->state_var.state_var2 > BOUNCE_ENDLAG)
            Fighter_EnterFall(fighter);
        return;
    }
    if (fd->state_var.state_var3)
    { // hit: small rebound, then the same end lag
        fd->phys.self_vel.Y = 2.2f;
        fd->state_var.state_var2 = 1;
        return;
    }
    if (FrameTimerCheck(fighter) == 0)
        Fighter_EnterFall(fighter);
}

void Bounce_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var2 > 0)
    {
        fd->phys.self_vel.Y = fd->phys.self_vel.Y - 0.15f;
        return;
    }
    fd->phys.self_vel.X = fd->phys.self_vel.X * 0.92f;
    float vy = fd->phys.self_vel.Y - BOUNCE_ACCEL;
    if (vy < BOUNCE_MAX)
        vy = BOUNCE_MAX;
    fd->phys.self_vel.Y = vy;
}

void Bounce_Land(GOBJ *fighter)
{ // touched the floor: rebound instead of landing
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var2 > 0)
    { // already rebounded once: land normally
        Fighter_EnterLanding(fighter);
        return;
    }
    Fighter_SetAirborne(fd);
    int n = fd->fighter_var.ft_var3; // bounces in a row so far; cleared in OnFrame once he stands on the floor
    if (n > BOUNCE_REBOUND_STEPS)
        n = BOUNCE_REBOUND_STEPS;
    fd->phys.self_vel.Y = BOUNCE_REBOUND + BOUNCE_REBOUND_STEP * (float)n;
    fd->fighter_var.ft_var3++;
    fd->state_var.state_var2 = 1;
}

void Bounce_Coll(GOBJ *fighter)
{
    Fighter_CollAir_IgnoreLedge(fighter, Bounce_Land);
}

// ---------------------------------------------------------------- shield: curled into the spin ball (v61)
// The game does not play the guard animations (it holds one pose) and ignores model changes in their scripts, so the ball
// model (visibility group 0, set 1) is switched here once a frame. 178 GuardOn, 179 Guard, 181 GuardSetOff (shield stun),
// 182 GuardReflect; 180 GuardOff shows the body again as he uncurls.
void OnFrame(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    int s = fd->state_id;
    if (s == 178 || s == 179 || s == 181 || s == 182)
    {
        Fighter_SetVisGroupCurrent(fighter, 0, 1);
        fd->fighter_var.ft_var1 = 1;
    }
    else if (fd->fighter_var.ft_var1)
    { // first frame out of the shield (shield drop, jump, roll, grab, hit): body back
        fd->fighter_var.ft_var1 = 0;
        Fighter_SetVisGroupCurrent(fighter, 0, 0);
    }
    // v64: Bounce Attack chain ends once he is on the floor in any other state
    if (fd->phys.air_state == 0 && s != ST_BOUNCE)
        fd->fighter_var.ft_var3 = 0;
    if (fd->phys.air_state == 0 || s == ASID_CLIFFCATCH || s == ASID_CLIFFWAIT)
    { // v70: on the floor or on a ledge: up B (Tails) and neutral B usable again
        fd->fighter_var.ft_var4 = 0;
        fd->fighter_var.ft_var5 = 0;
    }
    // Homing Attack lock-on reticle (SA1/SA2) on the target. v74: only while he is the ball homing in on someone (the dash
    // of the Homing Attack with a target, before it hits); v70-v73 showed it whenever he jumped or fell with it available.
    // Model part on bone 62 (visibility group 6), moved onto the target each frame.
    int ret = 0;
    if (s == ST_HOMING && fd->state_var.state_var2 && fd->state_var.state_var4 == 0 && fd->state_var.state_var1 <= HOMING_FRAMES)
    {
        float dx = 0, dy = 0;
        if (FindTarget(fighter, &dx, &dy))
        {
            JOBJ *j = fd->bones[62].joint;
            j->trans.X = 0.0f;
            j->trans.Y = dy + 7.0f;   // target centre (FindTarget measures from 6 above his feet) + 2
            j->trans.Z = dx * fd->facing_direction;
            JOBJ_SetMtxDirtySub(j);
            ret = 1;
        }
    }
    Fighter_SetVisGroupCurrent(fighter, 6, ret);
    // v64: eyelids (visibility group 4, set 1). A short blink every BLINK_PERIOD frames; shut while asleep (297-299),
    // dizzy after a shield break (211), flinching from a hit (75-91) and knocked down (183-185, 191-193).
    // Only while the normal body is showing (group 0, set 0): never on the spin ball.
    fd->fighter_var.ft_var2++;
    int shut = (fd->fighter_var.ft_var2 % BLINK_PERIOD) < BLINK_LEN;
    if ((s >= 297 && s <= 299) || s == 211 || (s >= 75 && s <= 91) || (s >= 183 && s <= 185) || (s >= 191 && s <= 193))
        shut = 1;
    if (fd->dobj_toggle[0].index != 0)
        shut = 0;
    int lid = shut ? 1 : (fd->dobj_toggle[3].index == 1 ? 2 : 0); // v70: half-closed eyes while the mouth is open (attack face)
    if (fd->dobj_toggle[0].index != 0)
        lid = 0;
    Fighter_SetVisGroupCurrent(fighter, 4, lid);
    // v75: after letting go, Tails (whole model on bone 62) flies up and forward and shrinks away over TAILS_FLYOFF frames
    int tails_vis = (s == ST_TAILS);
    if (fd->fighter_var.ft_var6 > 0 && s != ST_TAILS)
    {
        int t = fd->fighter_var.ft_var6++;
        JOBJ *tj = fd->bones[62].joint;
        float k = 1.0f - (float)t / (float)TAILS_FLYOFF;
        tj->trans.X = 0.0f;
        tj->trans.Y = TAILS_PIVOT_Y + 1.6f * (float)t;
        tj->trans.Z = TAILS_PIVOT_Z + 1.1f * (float)t;
        tj->scale.X = k; tj->scale.Y = k; tj->scale.Z = k;
        JOBJ_SetMtxDirtySub(tj);
        tails_vis = 1;
        if (t >= TAILS_FLYOFF)
            fd->fighter_var.ft_var6 = 0;
    }
    else if (s == ST_TAILS)
        fd->fighter_var.ft_var6 = 0;
    Fighter_SetVisGroupCurrent(fighter, 5, tails_vis);
    // v75: release window: after TAILS_WINDOW frames, the next time he is in a plain fall he goes into free fall
    if (fd->fighter_var.ft_var7 > 0)
    {
        if (fd->phys.air_state == 0 || s == ASID_CLIFFCATCH || s == ASID_CLIFFWAIT || (s >= ASID_DAMAGEHI1 && s <= ASID_DAMAGEFLYROLL) || s == ASID_DAMAGEFALL)
            fd->fighter_var.ft_var7 = 0; // landed, grabbed a ledge or got hit: no free fall
        else if (++fd->fighter_var.ft_var7 > TAILS_WINDOW && s >= ASID_FALL && s <= ASID_FALLAERIALB)
        {
            fd->fighter_var.ft_var7 = 0;
            Fighter_EnterSpecialFall(fighter, 1, 1, 0, 1.0f, 15.0f);
        }
    }
}

// ---------------------------------------------------------------- state table (state 341 + index)
__attribute__((used)) static struct FtState move_logic[] = {
    {302, 0x340511, 0x12, 0x0, Homing_Anim, 0, Homing_Phys, Homing_Coll, Fighter_UpdateCameraBox},   // 341 Homing Attack (anim SpecialAirN)
    {303, 0x341012, 0x13, 0x0, 0, Charge_IASA, Ground_Phys, Ground_Coll, Fighter_UpdateCameraBox},   // 342 Spin Dash charge (anim SpecialSStart)
    {304, 0x341012, 0x13, 0x0, Roll_Anim, Roll_IASA, Roll_Phys, Ground_Coll, Fighter_UpdateCameraBox}, // 343 Spin Dash roll (anim SpecialS)
    {308, 0x340613, 0x14, 0x0, Lsd_Anim, 0, Lsd_Phys, Lsd_Coll, Fighter_UpdateCameraBox},            // 344 Light Speed Dash (anim SpecialAirHi)
    {313, 0x340614, 0x15, 0x0, Bounce_Anim, 0, Bounce_Phys, Bounce_Coll, Fighter_UpdateCameraBox},   // 345 Bounce Attack (anim SpecialAirLw)
    {307, 0x340613, 0x14, 0x0, Lsd_Anim, 0, Lsd_Phys, Lsd_Coll, Fighter_UpdateCameraBox},            // 346 Light Speed Dash, sideways pose (anim SpecialHi)
    {305, 0x341012, 0x13, 0x0, LdCharge_Anim, 0, Ground_Phys, Ground_Coll, Fighter_UpdateCameraBox},   // 347 Light Dash pause, ground (anim SpecialAirSStart)
    {305, 0x341012, 0x13, 0x0, LdCharge_Anim, 0, LdChargeAir_Phys, Air_Coll, Fighter_UpdateCameraBox}, // 348 Light Dash pause, air
    {306, 0x341012, 0x13, 0x0, LdGround_Anim, 0, LdGround_Phys, Ground_Coll, Fighter_UpdateCameraBox}, // 349 Light Dash on the floor (anim SpecialAirS)
    {306, 0x341012, 0x13, 0x0, LdAir_Anim, 0, LdAir_Phys, Lsd_Coll, Fighter_UpdateCameraBox},          // 350 Light Dash in the air
    {309, 0x340613, 0x14, 0x0, Tails_Anim, 0, Tails_Phys, Lsd_Coll, Fighter_UpdateCameraBox},         // 351 Tails carry (anim SpecialHiCatch)
};

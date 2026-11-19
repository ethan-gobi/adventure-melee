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
#define ST_LSD_SIDE 346 // same move as 344 with the head-first flying pose, used when the dash is mostly sideways

#define HOMING_RANGE 75.0f
#define HOMING_SPEED 3.4f
#define HOMING_FRAMES 24
#define AIRDASH_SPEED 2.8f
#define AIRDASH_FRAMES 12
#define HOMING_ENDLAG 24 // extra frames after the dash where Sonic just falls and cannot act (v52: 14 -> 24)
#define HOMING_HITLAG 12 // frames after a hit, popping up and back, before he can act (v52: 0 -> 12)
#define BOUNCE_ENDLAG 18 // frames after the rebound before Sonic can act
#define ROLL_BASE 3.0f
#define ROLL_BONUS 1.6f
#define CHARGE_MAX 45
#define ROLL_FRAMES 34
#define LSD_SPEED 3.3f
#define LSD_FRAMES 12
#define LSD_END 22
#define BOUNCE_HOP 2.4f
#define BOUNCE_ACCEL 0.45f
#define BOUNCE_MAX -4.6f
#define BOUNCE_REBOUND 3.0f

#define INL static inline __attribute__((always_inline))

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
    else if (fd->jump.jumps_used > fd->attr.max_jumps)
        return; // already missed one this airtime (marker set in Homing_Anim); cleared by the game on landing
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
        fd->jump.jumps_used = fd->attr.max_jumps + 1;
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
    { // end lag: no steering, just slow down and fall
        fd->phys.self_vel.X = fd->phys.self_vel.X * 0.9f;
        fd->phys.self_vel.Y = fd->phys.self_vel.Y - 0.15f;
        return;
    }
    if (fd->state_var.state_var2)
    {
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
    if (t >= 8 && (!(fd->input.held & PAD_BUTTON_B) || t >= CHARGE_MAX + 15))
    {
        if (t > CHARGE_MAX)
            t = CHARGE_MAX;
        float speed = ROLL_BASE + ROLL_BONUS * (float)t / (float)CHARGE_MAX;
        EnterState(fighter, ST_ROLL);
        fd->phys.self_vel_ground.X = speed * fd->facing_direction;
    }
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
INL void LsdStart(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->phys.air_state == 0)
        Fighter_SetAirborne(fd);
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
    fd->phys.self_vel.X = LSD_SPEED * sx / len;
    fd->phys.self_vel.Y = LSD_SPEED * sy / len;
    float ax = sx < 0.0f ? -sx : sx, ay = sy < 0.0f ? -sy : sy;
    EnterState(fighter, (ax > ay * 1.2f) ? ST_LSD_SIDE : ST_LSD);
}

void SpecialHi(GOBJ *fighter) { LsdStart(fighter); }
void SpecialAirHi(GOBJ *fighter) { LsdStart(fighter); }

void Lsd_Anim(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    fd->state_var.state_var1++;
    if (fd->state_var.state_var1 > LSD_END || FrameTimerCheck(fighter) == 0)
        Fighter_EnterSpecialFall(fighter, 1, 1, 0, 1.0f, 15.0f);
}

void Lsd_Phys(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    if (fd->state_var.state_var1 > LSD_FRAMES)
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
    fd->phys.self_vel.Y = BOUNCE_REBOUND;
    fd->state_var.state_var2 = 1;
}

void Bounce_Coll(GOBJ *fighter)
{
    Fighter_CollAir_IgnoreLedge(fighter, Bounce_Land);
}

// ---------------------------------------------------------------- state table (state 341 + index)
__attribute__((used)) static struct FtState move_logic[] = {
    {302, 0x340511, 0x12, 0x0, Homing_Anim, 0, Homing_Phys, Air_Coll, Fighter_UpdateCameraBox},      // 341 Homing Attack (anim SpecialAirN)
    {303, 0x341012, 0x13, 0x0, 0, Charge_IASA, Ground_Phys, Ground_Coll, Fighter_UpdateCameraBox},   // 342 Spin Dash charge (anim SpecialSStart)
    {304, 0x341012, 0x13, 0x0, Roll_Anim, 0, Roll_Phys, Ground_Coll, Fighter_UpdateCameraBox},       // 343 Spin Dash roll (anim SpecialS)
    {308, 0x340613, 0x14, 0x0, Lsd_Anim, 0, Lsd_Phys, Lsd_Coll, Fighter_UpdateCameraBox},            // 344 Light Speed Dash (anim SpecialAirHi)
    {313, 0x340614, 0x15, 0x0, Bounce_Anim, 0, Bounce_Phys, Bounce_Coll, Fighter_UpdateCameraBox},   // 345 Bounce Attack (anim SpecialAirLw)
    {307, 0x340613, 0x14, 0x0, Lsd_Anim, 0, Lsd_Phys, Lsd_Coll, Fighter_UpdateCameraBox},            // 346 Light Speed Dash, sideways pose (anim SpecialHi)
    {305, 0x341012, 0x13, 0x0, LdCharge_Anim, 0, Ground_Phys, Ground_Coll, Fighter_UpdateCameraBox},   // 347 Light Dash pause, ground (anim SpecialAirSStart)
    {305, 0x341012, 0x13, 0x0, LdCharge_Anim, 0, LdChargeAir_Phys, Air_Coll, Fighter_UpdateCameraBox}, // 348 Light Dash pause, air
    {306, 0x341012, 0x13, 0x0, LdGround_Anim, 0, LdGround_Phys, Ground_Coll, Fighter_UpdateCameraBox}, // 349 Light Dash on the floor (anim SpecialAirS)
    {306, 0x341012, 0x13, 0x0, LdAir_Anim, 0, LdAir_Phys, Lsd_Coll, Fighter_UpdateCameraBox},          // 350 Light Dash in the air
};

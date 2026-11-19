// Sonic fighter code (m-ex), prototype v0.
// Neutral B = Homing Attack: launch toward the nearest opponent in range and spin (neutral-air hitbox).
// With no target in range Sonic does a short forward air dash. Uses the common neutral-air state for now,
// so the spin animation and hitbox are the neutral air's.
#include "../tools/m-ex/MexTK/include/mex.h"

#define HOMING_RANGE 70.0f   // units, measured centre to centre
#define HOMING_SPEED 3.2f    // units per frame at launch
#define DASH_SPEED_X 2.8f    // no-target forward dash
#define DASH_SPEED_Y 0.6f
#define CENTER_Y 5.0f        // aim at body centre, not feet
#define GROUND_HOP 1.0f      // minimum upward speed when starting on the ground (a level launch froze the game in v12/v13)

// Plain-C square root (Newton's method). Used instead of the game's sqrtf while testing homing,
// whose call path hung the game in v12.
static inline __attribute__((always_inline)) float SqrtNewton(float x)
{
    if (x <= 0.0f)
        return 0.0f;
    float g = (x > 1.0f) ? x * 0.5f : 1.0f;
    for (int i = 0; i < 12; i++)
        g = 0.5f * (g + x / g);
    return g;
}

static inline __attribute__((always_inline)) GOBJ *FindTarget(GOBJ *fighter, float *dx, float *dy)
{
    FighterData *fd = fighter->userdata;
    GOBJ *best = 0;
    float best_d2 = HOMING_RANGE * HOMING_RANGE;
    for (int i = 0; i < 6; i++)
    {
        GOBJ *g = Fighter_GetGObj(i);
        if (g == 0 || g == fighter)
            continue;
        FighterData *od = g->userdata;
        float x = od->phys.pos.X - fd->phys.pos.X;
        float y = (od->phys.pos.Y + CENTER_Y) - (fd->phys.pos.Y + CENTER_Y);
        float d2 = x * x + y * y;
        if (d2 < best_d2)
        {
            best_d2 = d2;
            best = g;
            *dx = x;
            *dy = y;
        }
    }
    return best;
}

static inline __attribute__((always_inline)) void HomingAttack(GOBJ *fighter)
{
    FighterData *fd = fighter->userdata;
    float dx = 0, dy = 0;
    GOBJ *target = FindTarget(fighter, &dx, &dy);

    int from_ground = (fd->phys.air_state == 0);
    if (from_ground)
        Fighter_SetAirborne(fd);

    if (target)
    {
        float len = SqrtNewton(dx * dx + dy * dy);
        // DIAG (test build): an invalid distance sends Sonic left and up so the test log shows it
        if (!(len > 1.0f && len < 200.0f))
        {
            fd->phys.self_vel.X = -2.0f;
            fd->phys.self_vel.Y = 2.0f;
            ActionStateChange(0, 1, 0, fighter, ASID_ATTACKAIRN, 0, 0);
            Fighter_AdvanceScript(fighter);
            return;
        }
        fd->facing_direction = (dx >= 0) ? 1.0f : -1.0f;
        fd->phys.self_vel.X = HOMING_SPEED * dx / len;
        fd->phys.self_vel.Y = HOMING_SPEED * dy / len;
        if (from_ground && fd->phys.self_vel.Y < GROUND_HOP)
            fd->phys.self_vel.Y = GROUND_HOP;
    }
    else
    {
        fd->phys.self_vel.X = DASH_SPEED_X * fd->facing_direction;
        fd->phys.self_vel.Y = DASH_SPEED_Y;
    }

    ActionStateChange(0, 1, 0, fighter, ASID_ATTACKAIRN, 0, 0);
    Fighter_AdvanceScript(fighter);
}

void SpecialN(GOBJ *fighter)
{
    HomingAttack(fighter);
}

void SpecialAirN(GOBJ *fighter)
{
    HomingAttack(fighter);
}

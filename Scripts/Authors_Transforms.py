'''
These transforms are those used by the author.
For early versions, these may be filled more with play than
actual good ideas for game modifications.
'''
# Import all transform functions.
from Plugins import *

# Adjust the exe to point at a saved copy, since X4.exe will be symlinked
# to the customized version.
Settings(X4_exe_name = 'X4_nonsteam.exe')
#Settings(X4_exe_name = 'X4.vanilla.exe')

Apply_Live_Editor_Patches()


# Exe edits.
# Disabled when not refreshing; the prior produced exe will not
# be deleted by the customizer.
if 0:
    Remove_Sig_Errors()
    Remove_Modified()

# Prune some mass traffic.
# (There may also be a way to adjust this in-game now.)
Adjust_Job_Count(('id masstraffic*', 0.5))

# Testing adjusting jobs globally.
#Adjust_Job_Count(('*', .0001))

# Toy around with coloring.
# This is Pious Mists.
# Color_Text((20005,3021,'C'))

# Speed up all smaller ships by a bit.
'''
Adjust_Ship_Speed(
    ('class ship_s' , 1.3),
    ('class ship_m' , 1.1),
    )
'''

# Toy around with small weapons.
'''
Adjust_Weapon_Damage(
    ('tags small standard weapon'   , 2),
    ('*'                            , 1.2),
    )
Adjust_Weapon_Range(
    ('tags small standard weapon'   , 2),
    ('tags missile'                 , 2),
    )
Adjust_Weapon_Shot_Speed(
    ('tags small standard weapon'   , 2),
    ('tags missile'                 , 2),
    )
Adjust_Weapon_Fire_Rate(
    ('tags small standard weapon'   , 4),
    #('tags missile'                 , 2),
    )
Print_Weapon_Stats()
'''


# Reduce general price spread on wares, to reduce trade profit.
# (Remove for now, until getting a better feel for the game.)
#Adjust_Ware_Price_Spread(0.5)

# Reduce the prices on inventory items, since they are often
# obtained for free.
#Adjust_Ware_Prices(('container inventory', 0.5) ) 
#Print_Ware_Stats()

# Reduce generic mission rewards somewhat heavily.
#Adjust_Mission_Rewards(0.3)
# Make mods more likely from missions.
#Adjust_Mission_Reward_Mod_Chance(3)

# Sector/speed rescaling stuff. Requires new game to work well.
if 1:
    # Slow down ai scripts a bit for better fps.
    # Note on 20k ships save 300km out of vision:
    #  1x/1x: 37 fps (vanilla)
    #  2x/4x: 41 fps (default args)
    #  4x/8x: 46 fps
    Increase_AI_Script_Waits(
        oov_multiplier = 2,
        oov_seta_multiplier = 4,
        oov_max_wait = 15,
        iv_multiplier = 1,
        iv_seta_multiplier = 2,
        iv_max_wait = 5,
        include_extensions = False,
        skip_combat_scripts = False,
        )


    # Disable travel drives for ai.
    Disable_AI_Travel_Drive()

    # Nerf travel speed for player.
    Remove_Engine_Travel_Bonus()

    # Enable seta when not piloting.
    # TODO: couldn't find a way to do this.

    # Retune radars to shorter range, for fps and for smaller sectors.
    Set_Default_Radar_Ranges(
        ship_xl       = 30,
        ship_l        = 30,
        ship_m        = 25,
        ship_s        = 20,
        ship_xs       = 20,
        spacesuit     = 15,
        station       = 30,
        satellite     = 20,
        adv_satellite = 30,
        )
    Set_Ship_Radar_Ranges(
        # Bump scounts back up. 30 or 40 would be good.
        ('type scout'  , 30),
        # Give carriers more stategic value with highest radar.
        ('type carrier', 40),
        )
    
    # Adjust engines to remove the split base speed advantage, and shift
    # the travel drive bonus over to base stats.
    # TODO: think about how race/purpose adjustments multiply; do any engines
    # end up being strictly superior to another?
    Rebalance_Engines(        
        race_speed_mults = {
            'argon'   : {'thrust' : 1,    'boost'  : 1,    'boost_time' : 1   },
            # Slightly better base speed, worse boost.
            'paranid' : {'thrust' : 1.05, 'boost'  : 0.80, 'boost_time' : 0.8 },
            # Fast speeds, short boost.
            'split'   : {'thrust' : 1.10, 'boost'  : 1.20, 'boost_time' : 0.6 },
            # Slower teladi speeds, but balance with long boosts.
            'teladi'  : {'thrust' : 0.95, 'boost'  : 0.90, 'boost_time' : 1.5 },
            },
        purpose_speed_mults = {
            'allround' : {'thrust' : 1,    'boost' : 1,    'boost_time' : 1,    },
            # Combat will be slowest but best boost.
            'combat'   : {'thrust' : 0.9,  'boost' : 1.5,  'boost_time' : 1.5,  },
            # Travel is fastest, worst boost.
            'travel'   : {'thrust' : 1.1,  'boost' : 0.5,  'boost_time' : 0.5,  },
            },
        )
    
    # Adjust speeds per ship class.
    # Note: vanilla averages and ranges are:    
    # xs: 130 (58 to 152)
    # s : 328 (71 to 612)
    # m : 319 (75 to 998)
    # l : 146 (46 to 417)
    # xl: 102 (55 to 164)
    # Try clamping variation to within 0.5x (mostly affects medium).
    # TODO: more fine-grain, by purpose (corvette vs frigate, etc.).
    Rescale_Ship_Speeds(match_all = ['type  scout' ],  average = 500, variation = 0.2)
    Rescale_Ship_Speeds(match_all = ['class ship_s'],  average = 400, variation = 0.25, 
                        match_none= ['type  scout'])
    Rescale_Ship_Speeds(match_all = ['class ship_m'],  average = 300, variation = 0.3)
    Rescale_Ship_Speeds(match_all = ['class ship_l'],  average = 200, variation = 0.4)
    # Ignore the python (unfinished).
    Rescale_Ship_Speeds(match_all = ['class ship_xl'], average = 150, variation = 0.4,
                        match_none= ['name ship_spl_xl_battleship_01_a_macro'])
    
    # Rescale the sectors.
    Scale_Sector_Size(
        # Whatever this is set to, want around 0.4 or less at 250 km sectors.
        scaling_factor                     = 0.4,
        scaling_factor_2                   = 0.3,
        transition_size_start              = 200000,
        transition_size_end                = 400000,
        precision_steps                    = 20,
        remove_ring_highways               = True,
        remove_nonring_highways            = False,
        extra_scaling_for_removed_highways = 0.7,
        )
    


# Write modified files.
Write_To_Extension()


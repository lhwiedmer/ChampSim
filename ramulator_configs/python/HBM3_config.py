import ramulator

frontend = ramulator.frontend.External(clock_ratio=1)

dram = ramulator.dram.HBM3(org_preset="HBM3_32Gb_8hi", timing_preset="HBM3_6400Mbps")
ctrl = ramulator.controller.HBM34(
    dram=dram,
    scheduler=ramulator.scheduler.FRFCFS(),
    refresh_manager=ramulator.refresh_manager.AllBank(),
    row_policy=ramulator.row_policy.Open(),
    addr_mapper=ramulator.addr_mapper.RoBaRaCoCh(),
)

mem = ramulator.memory_system.GenericDRAM(
    clock_ratio=1,
    controllers=[ctrl] * 16,
    channel_mapper=ramulator.channel_mapper.CacheLineInterleave(),
)

sim = ramulator.Simulation(frontend, mem)
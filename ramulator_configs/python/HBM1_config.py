import ramulator

frontend = ramulator.frontend.External(clock_ratio=1)

dram = ramulator.dram.HBM1(org_preset="HBM1_4Gb", timing_preset="HBM1_1Gbps")
ctrl = ramulator.controller.HBM12(
    dram=dram,
    scheduler=ramulator.scheduler.FRFCFS(),
    refresh_manager=ramulator.refresh_manager.AllBank(),
    row_policy=ramulator.row_policy.Open(),
    addr_mapper=ramulator.addr_mapper.RoBaRaCoCh(),
)

mem = ramulator.memory_system.GenericDRAM(
    clock_ratio=1,
    controllers=[ctrl] * 8,
    channel_mapper=ramulator.channel_mapper.CacheLineInterleave(),
)

sim = ramulator.Simulation(frontend, mem)
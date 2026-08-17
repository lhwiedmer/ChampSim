import ramulator

frontend = ramulator.frontend.External(clock_ratio=1)

dram = ramulator.dram.HBM4(org_preset="HBM4_32Gb_4Hi", timing_preset="HBM4_8000Mbps")
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
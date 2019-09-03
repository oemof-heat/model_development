from oemof.solph import Bus, Transformer, Sink, Flow


class Pipe():
    def __init__(self, label, inputs, outputs, loss_factor=1, losses_fixed=0):
        self.component_list = []

        self.bus = Bus(label=label + '_bus')

        self.trsf_in = Transformer(label=label + '_in',
                                   inputs=inputs,
                                   outputs={self.bus: Flow()},
                                   conversion_factors={self.bus: loss_factor})

        self.trsf_out = Transformer(label=label + '_out',
                                    inputs={self.bus: Flow()},
                                    outputs=outputs)

        self.losses = Sink(label=label + '_losses',
                           inputs={self.bus: Flow(nominal_value=1,
                                                  actual_value=losses_fixed,
                                                  fixed=True)})

        self.component_list.extend([self.bus,
                                    self.trsf_in,
                                    self.trsf_out,
                                    self.losses])

    def get_components(self):
        return self.component_list

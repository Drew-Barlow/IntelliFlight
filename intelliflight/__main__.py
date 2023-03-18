from .models.bayes_net import Bayes_Net

x = Bayes_Net('data/models/bayes_net.model.json')
# x.train_model('data/historical/flights/T_ONTIME_MARKETING.csv',
#              10, .02, .1, 33000897)
# x.export_parameters()

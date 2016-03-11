#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Copyright 2016 Nervana Systems Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------
"""
Small CIFAR10 based convolutional neural network. Showcases loading data
on-demand, conserving device memory while not compromising on speed.
"""

import os
from neon.data import DataLoader, ImageParams
from neon.initializers import Uniform
from neon.layers import Affine, Conv, Pooling, GeneralizedCost
from neon.models import Model
from neon.optimizers import GradientDescentMomentum
from neon.transforms import Misclassification, Rectlin, Softmax, CrossEntropyMulti
from neon.callbacks.callbacks import Callbacks
from neon.util.argparser import NeonArgparser

# parse the command line arguments
parser = NeonArgparser(__doc__)
args = parser.parse_args()

shape = dict(channel_count=3, height=30, width=30)
train_params = ImageParams(augment=True, **shape)
test_params = ImageParams(**shape)
common = dict(target_size=1, nclasses=10)
train_dir = os.path.join(args.data_dir, 'train')
test_dir = os.path.join(args.data_dir, 'test')
train = DataLoader(set_name='train', repo_dir=train_dir,
                   media_params=train_params, shuffle=True, **common)
test = DataLoader(set_name='test', repo_dir=test_dir,
                  media_params=test_params, shuffle=False, **common)

init_uni = Uniform(low=-0.1, high=0.1)
opt_gdm = GradientDescentMomentum(learning_rate=0.01,
                                  momentum_coef=0.9,
                                  stochastic_round=args.rounding)

layers = [Conv((5, 5, 16), init=init_uni, activation=Rectlin(), batch_norm=True),
          Pooling((2, 2)),
          Conv((5, 5, 32), init=init_uni, activation=Rectlin(), batch_norm=True),
          Pooling((2, 2)),
          Affine(nout=500, init=init_uni, activation=Rectlin(), batch_norm=True),
          Affine(nout=10, init=init_uni, activation=Softmax())]

cost = GeneralizedCost(costfunc=CrossEntropyMulti())
mlp = Model(layers=layers)

# configure callbacks
callbacks = Callbacks(mlp, eval_set=test, **args.callback_args)

mlp.fit(train, optimizer=opt_gdm, num_epochs=args.epochs, cost=cost, callbacks=callbacks)

print 'Misclassification error = %.1f%%' % (mlp.eval(test, metric=Misclassification())*100)

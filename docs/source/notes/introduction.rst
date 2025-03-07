Introduction
=======================

`*PyTorch Geometric Temporal* <https://github.com/benedekrozemberczki/pytorch_geometric_temporal>`_ is an temporal graph neural network extension library for `PyTorch Geometric <https://github.com/rusty1s/pytorch_geometric/>`_. It builds on open-source deep-learning and graph processing libraries. *PyTorch Geometric Temporal* consists of state-of-the-art deep learning and parametric learning methods to process spatio-temporal signals. It is the first open-source library for temporal deep learning on geometric structures. First, it provides discrete time graph neural networks on dynamic and static graphs. Second, it allows for spatio-temporal learning when the time is represented continuously without the use of discrete snapshots. Implemented methods cover a wide range of data mining (`WWW <https://www2021.thewebconf.org/>`_, `KDD <https://www.kdd.org/kdd2020/>`_), artificial intelligence and machine learning (`AAAI <http://www.aaai.org/Conferences/conferences.php>`_, `ICONIP <https://www.apnns.org/ICONIP2020/>`_, `ICLR <https://iclr.cc/>`_) conferences, workshops, and pieces from prominent journals. 
 

Citing
=======================
If you find *PyTorch Geometric Temporal* useful in your research, please consider adding the following citation:

.. code-block:: latex

    >@misc{pytorch_geometric_temporal,
           author = {Benedek, Rozemberczki and Paul, Scherer and Yixuan, He and Nicolas, Collignon},
           title = {{PyTorch Geometric Temporal}},
           year = {2020},
           publisher = {GitHub},
           journal = {GitHub repository},
           howpublished = {\url{https://github.com/benedekrozemberczki/pytorch_geometric_temporal}},
    }

We briefly overview the fundamental concepts and features of PyTorch Geometric Temporal through simple examples.

Data Structures
=============================

Discrete Dataset Iterators
--------------------------

PyTorch Geometric Tenporal offers data iterators for discrete time datasets which contain the temporal snapshots. There are two types of discrete time data iterators:

- ``StaticGraphDiscreteSignal`` - Is designed for discrete spatio-temporal signals defined on a **static** graph.
- ``DynamicGraphDiscreteSignal`` - Is designed for discrete spatio-temporal signals defined on a **dynamic** graph.


Static Graphs with Discrete Signal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The constructor of a ``StaticGraphDiscreteSignal`` object requires the following parameters:

- ``edge_index`` - A **single** ``NumPy`` array to hold the edge indices.
- ``edge_weight`` - A **single** ``NumPy`` array to hold the edge weights.
- ``features`` - A **list** of ``NumPy`` arrays to hold the vertex features for each time period.
- ``targets`` - A **list** of ``NumPy`` arrays to hold the vertex level targets for each time period.
 
Static Graphs with Dynamic Signal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The constructor of a ``DynamicGraphDiscreteSignal`` object requires the following parameters:

- ``edge_indices`` - A **list** of ``NumPy`` arrays to hold the edge indices.
- ``edge_weights`` - A **list** of ``NumPy`` arrays to hold the edge weights.
- ``features`` - A **list** of ``NumPy`` arrays to hold the vertex features for each time period.
- ``targets`` - A **list** of ``NumPy`` arrays to hold the vertex level targets for each time period.

Temporal Snapshots
^^^^^^^^^^^^^^^^^^ 

A discrete temporal snapshot is a PyTorch Geometric ``Data`` object. Please take a look at this `readme <https://pytorch-geometric.readthedocs.io/en/latest/notes/introduction.html#data-handling-of-graphs>`_ for the details. The returned temporal snapshot has the following attributes:

- ``edge_index`` - A PyTorch ``LongTensor`` of edge indices used for node feature aggregation (optional).
- ``edge_attr`` - A PyTorch ``FloatTensor`` of edge features used for weighting the node feature aggregation (optional).
- ``x`` - A PyTorch ``FloatTensor`` of vertex features (optional).
- ``y`` - A PyTorch ``FloatTensor`` or ``LongTensor`` of vertex targets (optional).

Benchmark Datasets
-------------------

We released and included a number of datasets which can be used for comparing the performance of temporal graph neural networks algorithms. The related machine learning tasks are node and graph level supervised learning.

Discrete Time Datasets
^^^^^^^^^^^^^^^^^^^^^^
In case of discrete time graph neural networks these datasets are as follows:

- `Hungarian Chickenpox Dataset. <https://pytorch-geometric-temporal.readthedocs.io/en/latest/modules/dataset.html#torch_geometric_temporal.data.dataset.chickenpox.ChickenpoxDatasetLoader>`_
- `PedalMe London Dataset. <https://pytorch-geometric-temporal.readthedocs.io/en/latest/modules/dataset.html#torch_geometric_temporal.data.dataset.pedalme.PedalMeDatasetLoader>`_
- `Pems Bay Dataset. <https://pytorch-geometric-temporal.readthedocs.io/en/latest/modules/dataset.html#torch_geometric_temporal.data.dataset.pems_bay.PemsBayDatasetLoader>`_
- `Metr LA Dataset. <https://pytorch-geometric-temporal.readthedocs.io/en/latest/modules/dataset.html#torch_geometric_temporal.data.dataset.metr_la.METRLADatasetLoader>`_


The Hungarian Chickenpox Dataset can be loaded by the following code snippet. The ``dataset`` returned by the public ``get_dataset`` method is a ``StaticGraphDiscreteSignal`` object. 

.. code-block:: python

    from torch_geometric_temporal.data.dataset import ChickenpoxDatasetLoader

    loader = ChickenpoxDatasetLoader()

    dataset = loader.get_dataset()

Train-Test Splitter
-------------------


Discrete Train-Test Splitter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We provide functions to create temporal splits of the discrete time iterators. These functions return train and test data iterators which split the original iterator using a fix ratio. Snapshots from the earlier time periods from the training dataset and snapshots from the later periods form the test dataset. This way temporal forecasts can be evaluated in a real life like scenario. The function ``discrete_train_tes_split`` takes either a ``StaticGraphDiscreteSignal`` or a ``DynamicGraphDiscreteSignal`` and returns two iterattors according to the split ratio specified by ``train_ratio``.

.. code-block:: python

    from torch_geometric_temporal.data.dataset import ChickenpoxDatasetLoader
    from torch_geometric_temporal.data.splitter import discrete_train_test_split

    loader = ChickenpoxDatasetLoader()

    dataset = loader.get_dataset()

    train_dataset, test_dataset = discrete_train_test_split(dataset, train_ratio=0.8)



Applications
=============

In the following we will overview two case studies where PyTorch Geometric Temporal can be used to solve real world relevant machine learning problems. One of them is on discrete time spatial data and the other one uses continuous time graphs.   

Learning from a Discrete Temporal Signal
-------------------------------------------

We are using the Hungarian Chickenpox Cases dataset in this case study. We will train a regressor to predict the weekly cases reported by the counties using a recurrent graph convolutional network. First, we will load the dataset and create an appropriate spatio-temporal split.

.. code-block:: python

    from torch_geometric_temporal.data.dataset import ChickenpoxDatasetLoader
    from torch_geometric_temporal.data.splitter import discrete_train_test_split

    loader = ChickenpoxDatasetLoader()

    dataset = loader.get_dataset()

    train_dataset, test_dataset = discrete_train_test_split(dataset, train_ratio=0.2)

In the next steps we will define the **recurrent graph neural network** architecture used for solving the supervised task. The constructor defines a ``DCRNN`` layer and a feedforward layer. It is important to note that the final non-linearity is not integrated into the recurrent graph convolutional operation. This design principle is used consistently and it was taken from PyTorch Geometric. Because of this, we defined a ``ReLU`` non-linearity between the recurrent and linear layers manually. The final linear layer is not followed by a non-linearity as we solve a regression problem with zero-mean targets.

.. code-block:: python

    import torch
    import torch.nn.functional as F
    from torch_geometric_temporal.nn.recurrent import DCRNN

    class RecurrentGCN(torch.nn.Module):
        def __init__(self, node_features):
            super(RecurrentGCN, self).__init__()
            self.recurrent = DCRNN(node_features, 32, 1)
            self.linear = torch.nn.Linear(32, 1)

        def forward(self, x, edge_index, edge_weight):
            h = self.recurrent(x, edge_index, edge_weight)
            h = F.relu(h)
            h = self.linear(h)
            return h

Let us define a model (we have 4 node features) and train it on the training split (first 20% of the temporal snapshots) for 200 epochs. We backpropagate when the loss from every temporal snapshot is accumulated. We will use the **Adam optimizer** with a learning rate of **0.01**. The ``tqdm`` function is used for measuring the runtime need for each training epoch.

.. code-block:: python

    from tqdm import tqdm

    model = RecurrentGCN(node_features = 4)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    model.train()

    for epoch in tqdm(range(200)):
        cost = 0
        for time, snapshot in enumerate(train_dataset):
            y_hat = model(snapshot.x, snapshot.edge_index, snapshot.edge_attr)     
            cost = cost + torch.mean((y_hat-snapshot.y)**2)
        cost = cost / (time+1)
        cost.backward()
        optimizer.step()
        optimizer.zero_grad()

Using the holdout we will evaluate the performance of the trained recurrent graph convolutional network and calculate the mean squared error across **all of the spatial units and time periods**. 

.. code-block:: python

    model.eval()
    cost = 0
    for time, snapshot in enumerate(test_dataset):
        y_hat = model(snapshot.x, snapshot.edge_index, snapshot.edge_attr)
        cost = cost + torch.mean((y_hat-snapshot.y)**2)
    cost = cost / (time+1)
    cost = cost.item()
    print("MSE: {:.4f}".format(cost))
    >>> Accuracy: 0.6866

Learning from a Continuous Temporal Signal
-------------------------------------------

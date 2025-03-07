import math
import torch
from torch_geometric.utils import to_dense_adj
from torch_geometric.nn.conv import MessagePassing


def glorot(tensor):
    if tensor is not None:
        stdv = math.sqrt(6.0 / (tensor.size(-2) + tensor.size(-1)))
        tensor.data.uniform_(-stdv, stdv)

def zeros(tensor):
    if tensor is not None:
        tensor.data.fill_(0)

# Diffusion Convolution Layer
class DConv(MessagePassing):
    r"""An implementation of the Diffusion Convolution Layer. 
    For details see: `"Diffusion Convolutional Recurrent Neural Network:
    Data-Driven Traffic Forecasting" <https://arxiv.org/abs/1707.01926>`_

    Args:
        in_channels (int): Number of input features.
        out_channels (int): Number of output features.
        K (int): Filter size :math:`K`.
        bias (bool, optional): If set to :obj:`False`, the layer 
            will not learn an additive bias (default :obj:`True`)

    """

    def __init__(self, in_channels, out_channels, K, bias=True):
        super(DConv, self).__init__(aggr='add', flow="source_to_target")
        assert K > 0
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.weight = torch.nn.Parameter(torch.Tensor(2, K, in_channels, out_channels))

        if bias:
            self.bias = torch.nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)

        self.reset_parameters()

    def reset_parameters(self):
        glorot(self.weight)
        zeros(self.bias)

    def forward(self, x, edge_index, edge_weight):
        adj_mat = to_dense_adj(edge_index, edge_attr=edge_weight)
        adj_mat = adj_mat.reshape(adj_mat.size(1), adj_mat.size(2))
        deg_out = torch.matmul(adj_mat, torch.ones(size=(adj_mat.size(0), 1)).to(x.device))
        deg_out = deg_out.flatten()
        deg_in = torch.matmul(torch.ones(size=(1, adj_mat.size(0))).to(x.device), adj_mat)
        deg_in = deg_in.flatten()

        deg_out_inv = torch.reciprocal(deg_out)
        deg_in_inv = torch.reciprocal(deg_in)
        row, col = edge_index
        norm_out = deg_out_inv[row]
        norm_in = deg_in_inv[row] # row for W^T

        Tx_0 = x
        Tx_1 = x
        out = torch.matmul(Tx_0, (self.weight[0])[0]) + torch.matmul(Tx_0, (self.weight[1])[0]) 

        # propagate_type
        if self.weight.size(1) > 1:
            Tx_1_o = self.propagate(edge_index, x=x, norm=norm_out, size=None)
            Tx_1_i = self.propagate(edge_index, x=x, norm=norm_in, size=None)
            out = out + torch.matmul(Tx_1_o, (self.weight[0])[1]) + torch.matmul(Tx_1_i, (self.weight[1])[1])

        for k in range(2, self.weight.size(1)):
            Tx_2_o = self.propagate(edge_index, x=Tx_1_o, norm=norm_out, size=None)
            Tx_2_o = 2. * Tx_2_o - Tx_0
            Tx_2_i = self.propagate(edge_index, x=Tx_1_i, norm=norm_in, size=None) 
            Tx_2_i = 2. * Tx_2_i - Tx_0
            out = out + torch.matmul(Tx_2_o, (self.weight[0])[k]) + torch.matmul(Tx_2_i, (self.weight[1])[k])
            Tx_0, Tx_1_o, Tx_1_i = Tx_1, Tx_2_o, Tx_2_i

        if self.bias is not None:
            out += self.bias

        return out

    def message(self, x_j, norm):
        return norm.view(-1, 1) * x_j

    def __repr__(self):
        return '{}({}, {}, K={})'.format(self.__class__.__name__,
            self.in_channels, self.out_channels, self.weight.size(0))

class DCRNN(torch.nn.Module):
    r"""An implementation of the Diffusion Convolutional Gated Recurrent Unit.
    For details see: `"Diffusion Convolutional Recurrent Neural Network:
    Data-Driven Traffic Forecasting" <https://arxiv.org/abs/1707.01926>`_

    Args:
        in_channels (int): NUmber of input features.
        out_channels (int): Number of output features.
        K (int): Filter size :math:`K`.
        bias (bool, optional): If set to :obj:`False`, the layer 
            will not learn an additive bias (default :obj:`True`)

    """

    def __init__(self, in_channels: int, out_channels: int, K: int, bias: bool=True):
        super(DCRNN, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.K = K
        self.bias = bias

        self._create_parameters_and_layers()

    def _create_update_gate_parameters_and_layers(self):
        self.conv_x_z = DConv(in_channels=self.in_channels+self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K,
                                 bias=self.bias)


    def _create_reset_gate_parameters_and_layers(self):
        self.conv_x_r = DConv(in_channels=self.in_channels+self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K,
                                 bias=self.bias)


    def _create_candidate_state_parameters_and_layers(self):
        self.conv_x_h = DConv(in_channels=self.in_channels+self.out_channels,
                                 out_channels=self.out_channels,
                                 K=self.K,
                                 bias=self.bias)

    def _create_parameters_and_layers(self):
        self._create_update_gate_parameters_and_layers()
        self._create_reset_gate_parameters_and_layers()
        self._create_candidate_state_parameters_and_layers()    

    def _set_hidden_state(self, X, H):
        if H is None:
            H = torch.zeros(X.shape[0], self.out_channels).to(X.device)
        return H

    def _calculate_update_gate(self, X, edge_index, edge_weight, H):
        Z = torch.cat([X,H], dim=1)
        Z = self.conv_x_z(Z, edge_index, edge_weight)
        Z = torch.sigmoid(Z)
        return Z

    def _calculate_reset_gate(self, X, edge_index, edge_weight, H):
        R = torch.cat([X,H], dim=1)
        R = self.conv_x_r(R, edge_index, edge_weight)
        R = torch.sigmoid(R)
        return R

    def _calculate_candidate_state(self, X, edge_index, edge_weight, H, R):
        H_tilde = torch.cat([X, H * R], dim=1)
        H_tilde = self.conv_x_h(H_tilde, edge_index, edge_weight)
        H_tilde = torch.tanh(H_tilde)
        return H_tilde

    def _calculate_hidden_state(self, Z, H, H_tilde):
        H = Z * H + (1 - Z) * H_tilde
        return H

    def forward(self, X: torch.FloatTensor, edge_index: torch.LongTensor,
                edge_weight: torch.FloatTensor=None, H: torch.FloatTensor=None) -> torch.FloatTensor:
        r"""Making a forward pass. If edge weights are not present the forward pass
        defaults to an unweighted graph. If the hidden state matrix is not present
        when the forward pass is called it is initialized with zeros.

        Args:
            X (PyTorch Float Tensor): Node features.
            edge_index (PyTorch Long Tensor): Graph edge indices.
            edge_weight (PyTorch Long Tensor, optional): Edge weight vector.
            H (PyTorch Float Tensor, optional): Hidden state matrix for all nodes.

        Return types:
            H (PyTorch Float Tensor): Hidden state matrix for all nodes.
        """
        H = self._set_hidden_state(X, H)
        Z = self._calculate_update_gate(X, edge_index, edge_weight, H)
        R = self._calculate_reset_gate(X, edge_index, edge_weight, H)
        H_tilde = self._calculate_candidate_state(X, edge_index, edge_weight, H, R)
        H = self._calculate_hidden_state(Z, H, H_tilde)
        return H

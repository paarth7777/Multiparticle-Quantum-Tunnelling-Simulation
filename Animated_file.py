import pennylane as qml
import numpy as np
import random


num_qubits = 3  # For a single particle

dev = qml.device("default.qubit", num_qubits * 2)

d = 2 ** (num_qubits - 1) * 3


def controlledUnitary(unitary: np.ndarray, control_wires: list, control_values: list,
                      target_wire: int):
    """
    Precondition:
    - len(control_wires) == len(control_values)
    """

    if len(control_wires) != len(control_values):
        raise IndexError

    for i in range(len(control_wires)):
        if not control_values[i]:
            qml.PauliX(control_wires[i])

    qml.QubitUnitary(unitary, wires=control_wires + [target_wire])

    for i in range(len(control_wires)):
        if not control_values[i]:
            qml.PauliX(control_wires[i])


def potential_function(x1, x2):
    if x1 != x2:
        return 50 * num_qubits * 2 / abs(x1 - x2)

    return 0


def kinetic_function(k):
    return (1 * k) ** 2


def kinetic_energy_operator(dt):

    qml.QFT(range(num_qubits, 2 * num_qubits))
    qml.QFT(range(num_qubits))
    for i in range(2 ** (num_qubits - 1)):
        binary_str = format(i, '0' + str(num_qubits - 1) + 'b')
        diagonal = np.ndarray((2 ** num_qubits,), dtype=complex)
        for d in range(len(diagonal)):
            diagonal[d] = 1
        diagonal[-2] = np.exp(- 1j * dt * kinetic_function(2 * i))
        diagonal[-1] = np.exp(- 1j * dt * kinetic_function(2 * i + 1))
        controlledUnitary(np.diag(diagonal), list(range(num_qubits - 1)),
                          [int(j) for j in binary_str], num_qubits - 1)
        controlledUnitary(np.diag(diagonal), list(range(num_qubits, 2 * num_qubits - 1)),
                          [int(j) for j in binary_str], 2 * num_qubits - 1)
        # qml.ControlledQubitUnitary(np.diag([np.exp(-1j * dt * (2 * i)**2), np.exp(-1j * dt * (2 * i + 1)**2)]), control_wires=range(num_qubits -1), wires=num_qubits-1, control_values=binary_str)
    qml.adjoint(qml.QFT)(range(num_qubits))
    qml.adjoint(qml.QFT)(range(num_qubits, 2 * num_qubits))


def potential_energy_operator(dt):
    # double well potential

    for x1 in range(2 ** num_qubits):
        binary_str_x1 = format(x1, "0" + str(num_qubits) + "b")
        for x2 in range(2 ** (num_qubits - 1)):
            binary_str_x2 = format(x2, "0" + str(num_qubits - 1) + "b")
            diagonal = np.ndarray((2 ** (2 * num_qubits),), dtype=complex)
            for d in range(len(diagonal)):
                diagonal[d] = 1
            diagonal[-2] = np.exp(- 1j * dt * potential_function(x1, 2 * x2))
            diagonal[-1] = np.exp(- 1j * dt * potential_function(x1, 2 * x2 + 1))
            controlledUnitary(np.diag(diagonal), list(range(2 * num_qubits - 1)),
                              [int(j) for j in (binary_str_x1 + binary_str_x2)], 2 * num_qubits - 1)


def hamiltonian(dt):
    kinetic_energy_operator(dt)
    potential_energy_operator(dt)


@qml.qnode(dev)
def tunnelling_circuit(dt, t):
    starting_pos = np.zeros((2 * num_qubits,))
    for i in range(num_qubits, 2 * num_qubits):
        starting_pos[i] = 1
    qml.BasisState(starting_pos, wires=range(2 * num_qubits))
    for i in range(t):
        hamiltonian(dt)
    return qml.probs()

img1 = []
img2 = []
img = []
tunnelling_probs = []

import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

unit = screen.get_width() / 9

particle1_pos = pygame.Vector2(screen.get_width() / 9, screen.get_height() / 3)
particle2_pos = pygame.Vector2(8 * screen.get_width() / 9, 2 * screen.get_height() / 3)

tunnelled = False

white = (255, 255, 255)
green = (0, 255, 0)
blue = (0, 0, 128)

font = pygame.font.Font('freesansbold.ttf', 32)

# create a text surface object,
# on which text is drawn on it.
text = font.render('Tunnelled!', True, green, blue)

# create a rectangular object for the
# text surface object
textRect = text.get_rect()

# set the center of the rectangular object.
textRect.center = (screen.get_width() // 2, screen.get_height() // 2)

for i in range(50):
    results = tunnelling_circuit(1 / 50, i)
    # print(len(results))
    # p1_pos_probs = [sum([results[2 ** num_qubits * k + j].numpy() for j in range(2 ** num_qubits)]) for k in range(2 ** num_qubits)]
    # p2_pos_probs = [sum([results[2 ** num_qubits * j + k].numpy() for j in range(2 ** num_qubits)]) for k in range(2 ** num_qubits)]
    # for i in range(num_qubits):
    #     img1.append([])
    p = random.randint(0, 100) / 100
    cumulativeProbability = 0
    if not tunnelled:
        for j in range(len(results)):
            cumulativeProbability += results[j]
            if (p <= cumulativeProbability):
                x1 = j // 2 ** num_qubits
                x2 = j - x1

                if x1 == x2:
                    tunnelled = True
                    print("tunnelled!")

                particle1_pos = pygame.Vector2((x1 + 1) * screen.get_width() // 9, screen.get_height() // 3)
                particle2_pos = pygame.Vector2((x2 + 1) * screen.get_width() // 9, 2 * screen.get_height() // 3)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # fill the screen with a color to wipe away anything from last frame
                screen.fill("purple")

                pygame.draw.circle(screen, "red", particle1_pos, 20)
                pygame.draw.circle(screen, "blue", particle2_pos, 20)

                pygame.display.flip()
                break
    else:
        screen.fill("purple")
        screen.blit(text, textRect)
        pygame.display.flip()
    # tunnelling_probs.append(sum([sum(results[2 ** num_qubits * k + j].numpy() for j in range(2 ** num_qubits) if j == k) for k in range(2 ** num_qubits)]))
    img.append(results)


screen.fill("purple")
screen.blit(text, textRect)
pygame.display.flip()

pygame.quit()

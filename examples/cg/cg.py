import argparse
import contextlib
import time

import numpy as np
from scipy.sparse.linalg import cg
import six

import cupy


@contextlib.contextmanager
def timer(message):
    cupy.cuda.Stream.null.synchronize()
    start = time.time()
    yield
    cupy.cuda.Stream.null.synchronize()
    end = time.time()
    print('%s:  %f sec' % (message, end - start))


def fit(A, b, x0, tol, max_iter):
    xp = cupy.get_array_module(A)
    x = x0
    r0 = b - xp.dot(A, x)
    p = r0
    for i in six.moves.range(max_iter):
        a = xp.dot(r0.T, r0) / xp.dot(xp.dot(p.T, A), p)
        x += p * a
        r1 = r0 - xp.dot(A * a, p)
        if xp.linalg.norm(r1) < tol:
            return x
        b = xp.dot(r1.T, r1) / xp.dot(r0.T, r0)
        p = r1 + b * p
        r0 = r1
    msg = 'Failed to converge. Increase max-iter or tol.'
    print(msg)
    return x


def run(gpuid, tol, max_iter):
    N = 1000
    max_val = 100
    tri1 = np.tri(N) * np.random.randint(max_val, size=(N, N))
    tri2 = np.flipud(np.rot90(tri1))
    A = (tri1 + tri2).astype(np.float32)
    b = np.random.randint(max_val, size=N).astype(np.float32)
    x0 = np.zeros(N, dtype=np.float32)
    print('b =')
    print(b[:10])

    with timer(' CPU '):
        print()
        x = fit(A, b, x0, tol, max_iter)
        b_calc = np.dot(A, x)
        print(b_calc[:10])

    with cupy.cuda.Device(gpuid):
        A = cupy.asarray(A)
        b = cupy.asarray(b)
        x0 = cupy.asarray(x0)
        with timer(' GPU '):
            print()
            x = fit(A, b, x0, tol, max_iter)
            b_calc = cupy.dot(A, x)
            print(b_calc[:10])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu-id', '-g', default=0, type=int,
                        help='ID of GPU.')
    parser.add_argument('--tol', '-t', default=1.0e-5, type=float,
                        help='tolerance to stop iteration')
    parser.add_argument('--max-iter', '-m', default=100000000, type=int,
                        help='number of iterations')
    args = parser.parse_args()
    run(args.gpu_id, args.tol, args.max_iter)

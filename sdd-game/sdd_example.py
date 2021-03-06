"""Construct an SDD with n variables in which every model has exactly r true variables.

Print out the models.
"""

#!/usr/bin/python
import sdd
import sys
from inf import models


def r_in_n(manager, r, n, cur=1):
    """Construct an SDD corresponding to exactly r of n variables being true.

    Set r of the variables in the range [cur, cur+1, ..., n] to true.

    Args:
        r: The number of remaining variables to set to true
        n: The total number of variables in the SDD.
        cur: The current variable to set

    Returns:
        An SDD in which r of the variables in the range [cur, cur+1, ..., n] are true.
        The rest of the variables in that range are false.
    """
    alpha = sdd.sdd_manager_true(manager)
    if cur == n+1:
        pass

    elif r == 0:
        for i in range(cur, n+1):
            lit = sdd.sdd_manager_literal(-i, manager)
            alpha = sdd.sdd_conjoin(alpha, lit, manager)

    elif r == n - cur + 1:
        for i in range(cur, n+1):
            lit = sdd.sdd_manager_literal(i, manager)
            alpha = sdd.sdd_conjoin(alpha, lit, manager)

    else:
        beta = sdd.sdd_manager_literal(cur, manager)
        remainder_true = r_in_n(manager, r-1, n, cur+1)
        beta = sdd.sdd_conjoin(beta, remainder_true, manager)
        gamma = sdd.sdd_manager_literal(-cur, manager)
        remainder_false = r_in_n(manager, r, n, cur+1)
        gamma = sdd.sdd_conjoin(gamma, remainder_false, manager)
        alpha = sdd.sdd_disjoin(beta, gamma, manager)

    return alpha


def start_manager(num_vars):
    """Construct an SDD manager with num_vars variables.

    Args:
        num_vars: The number of variables to use in the SDD.

    Returns:
        An initialized SDD manager with a right vtree.
    """
    vtree = sdd.sdd_vtree_new(num_vars, "right")
    manager = sdd.sdd_manager_new(vtree)
    sdd.sdd_vtree_free(vtree)
    return manager


def main():
    if len(sys.argv) != 3:
        print "usage: %s [NUM-VARS] [NUM-TRUES]" % sys.argv[0]
        exit(1)
    num_vars, num_trues = (int(sys.argv[1]), int(sys.argv[2]))
    manager = start_manager(num_vars)
    alpha = r_in_n(manager, num_trues, num_vars)

    for model in models.models(alpha, sdd.sdd_manager_vtree(manager)):
        print models.str_model(model,var_count=num_vars)


if __name__ == '__main__':
    main()

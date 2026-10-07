# The fixed point

_The most important file in this repository. Read it before anything else; every change is judged against it. It is never shipped and never part of the kernel: the kernel does not state it, it is built from it. Changed only by the owner. Written down 2026-10-01 from the owner's words._

**The assumed reader of the kernel is someone who knows nothing about AI, wants to use it, and trusts whoever published it — or hopes they can.** That trust is a serious responsibility, and it is the kernel's to earn, not the reader's to verify.

Consequences:

- v0.0.1 has one job: prove reliability and safety for that person. Features come after.
- We do not dazzle, and we do not read the pulse of people anxious about missing out on AI. No claim without evidence (PHILOSOPHY #12); every public statement names the model-call exception; "Not claimed" stays in the release.
- Safe without understanding: defaults fail closed, a fresh policy refuses egress until the owner decides, everything is private until raised by a person, nothing is deleted. The reader need not know why for it to hold.
- The proof is for an aware owner and an aware agent (`.agents/decisions/2026-10-01_leakage-rule.md`, addendum). Against a person who sets out to leak their own data the kernel claims nothing.
- The kernel is the soul; tools are conveniences the reader may skip. A guarantee that only the tools can keep is not a guarantee of the kernel.
- The second person of gate G5 is this reader — a non-expert — not another developer.

The kernel may be improved later. This point does not move.

## The main philosophy of this repository (owner, 2026-10-03)

The fixed point is the main development philosophy of this repository, not one principle among several. When a change, a tool or a decision would break it, there are two honest answers only:

1. **Keep the point** — the change is wrong, however convenient; undo or redesign it.
2. **Start a new repository** — if the point itself must move, it is a different project with a different reader, and it gets its own repository and its own fixed point.

Quietly bending the point inside this repository is not an option. A convenience never outranks it; neither does consistency with a tool's defaults.

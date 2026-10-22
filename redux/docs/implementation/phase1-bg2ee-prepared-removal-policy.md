# BG2EE prepared spell removal policy

A charged prepared spell in BG2EE now binds its existing ordinary unmemorize callback directly. GUIMG/GUIPR retain the confirmation callback when the game is not BG2EE; depleted-entry behavior is unchanged. The wizard binding remains inside the existing non-Sorcerer branch. No spell grant, recharge, casting, spellbook serialization or combat behavior changes.

Original wizard physical-UI observation and saved level-2 bytes support immediate removal without a modal. Shipped ui.menu unmemorizeMageSpell/unmemorizePriestSpell directly dispatch the selected prepared entry. Eligible original priest operation remains source-supported, not runtime measured. Independent reference audit: testing/phase1-original-spellbook-independent-audit.md. The old native confirmation journeys and original failures remain historical BEFORE results.

The focused test source executes the actual parsed callback-selection source branch against both game policies and both charged/depleted flags, verifies the wizard nonspontaneous guard, and retains Classic confirmation functions. This delivery was source-only: no tests, builds or runtimes were executed. An explicit AFTER journey is a separate external change; fresh coherent candidate engine and external receipts are required before runtime claims.


Coordinator execution now passes the explicit EE-direct stock and private
name-control journeys on coherent candidate `20261022T093226Z-candidate-5a60a03d`.
The [stock raw audit](../testing/phase1-ee-direct-stock-independent-audit.md)
and [controlled-name audit](../testing/phase1-ee-direct-name-control-independent-audit.md)
independently confirm actual immediate charged removal without modal, depleted
re-add, exact saved spell identities and fresh-process reload. Original eligible
priest interaction and Classic runtime remain unmeasured; the source/branch tests
preserve Classic callback selection without claiming a new Classic native pass.

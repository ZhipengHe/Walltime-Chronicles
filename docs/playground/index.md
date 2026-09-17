---
hide:
  - navigation
  - toc
---

# The Playground

> *Every interactive piece on the site, at full size.*

The articles embed these pieces in a column they share with the navigation, and some of them lose room there. Here each one gets the whole width. The explanation stays with its article, linked from each block, so this page is a gallery and nothing more.

---

## :material-podium: The Queue Is Not a Line

### Score explorer {#score-explorer}

Set a request, a recent usage and a waiting time, and read each term of Aqua's `job_sort_formula` as it changes. Explained in [Putting It Together](../scheduler/The-Queue-Is-Not-a-Line.md#explorer).

<!-- markdownlint-disable MD033 -->
<div id="queue-score-explorer" class="qse"></div>
<!-- markdownlint-enable MD033 -->

### Backfill on all thirteen H100 nodes {#backfill}

Two invented days on the thirteen H100 nodes of `gpu_batch_exec`, about 160 jobs, with Aqua's published scheduler settings: a cycle every 60 seconds and five bookings. Green bars are fillers, each ending before the booking on its GPU, and the dashed line in the queue marks where bookings stop. Fair-share factors are assumed. Explained in [Backfill: How a Lower-Ranked Job Starts First](../scheduler/The-Queue-Is-Not-a-Line.md#backfill).

<!-- markdownlint-disable MD033 -->
<div id="backfill-animation" class="bfa bfa-full" data-nodes="13" data-arrivals="3.2" data-queue="20" data-slots="10" data-log="5"></div>
<!-- markdownlint-enable MD033 -->

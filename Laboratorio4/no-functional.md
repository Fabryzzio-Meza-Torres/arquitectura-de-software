# Original non-functional-requirement notes — superseded

These translated notes preserve the initial input. The reconciled and authoritative backlog
is [`requirements/no-functional-requirements.md`](requirements/no-functional-requirements.md).

## Architecture and connectivity

- **RNF-1:** The solution must use local networks for each school, with a departmental server
  between the central level in Lima and each school's server laptop.
- **RNF-2:** Users must be able to access the platform through the school LAN during class
  without requiring internet on every classroom laptop.
- **RNF-3:** The system must ensure delivery of large files through automatic retry after a
  transfer failure.
- **RNF-4:** The system must support batch data processing and synchronization to tolerate
  connectivity loss and retain information backups.
- **RNF-5:** The system must automatically delete files at the close of each two-month period
  to free storage.

## Modularity and user experience

- **RNF-6:** The system must be organized into well-defined, decoupled modules and components.
- **RNF-7:** Development must prioritize the experience of end users.
- **RNF-8:** The interface must be intuitive and easy to use for every user role.

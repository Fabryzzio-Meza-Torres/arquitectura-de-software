# Out of scope (out of scope)

Restated from [Staged scope](StagedScope.md) so it stands as its own gate: nothing in the
requirement set may implement any of the following, in any phase.

- **The equipment provider as an actor, screen, API or flow.** Choosing the machine and the
  provider is a commercial negotiation that happens entirely outside the platform, before the
  client company ever opens it. See [Key product decisions](KeyProductDecisions.md) KPD-2.
- **Equipment procurement, supply-chain management or delivery logistics.** The leasing
  company's purchase of the equipment from the provider is external and offline. Inside the
  system, equipment delivery appears at most as a status update, never as an orchestrated
  flow.
- **A marketplace or machine-selection tool.** The platform does not help either party find
  or choose equipment or a provider.
- **Direct information or advice from a risk analyst.** The risk analyst is not a system
  actor; a broker may relay guidance informally, but the platform never models that role.
- **The transactional credit-decisioning engine itself.** The platform orchestrates and
  tracks the credit outcome (approved / conditioned / rejected); it never computes the
  decision. See [Key product decisions](KeyProductDecisions.md) KPD-8.

A requirement that implements any of the above is a scope-creep defect, not extra coverage
(see `agents/eval-spec.md`, Step 2).

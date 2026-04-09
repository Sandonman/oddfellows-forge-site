# Reset Policy — project-template-sample

Use phase checkpoints to control safe auto-reset:

- build start   => busy (no auto-reset)
- build done    => safe
- qa start      => busy
- qa done       => safe
- release start => busy
- release done  => safe

Commands:

```bash
./scripts/project-phase-checkpoint.sh project-template-sample build start
./scripts/project-phase-checkpoint.sh project-template-sample build done
```

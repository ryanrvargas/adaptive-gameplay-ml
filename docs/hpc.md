# Using the HPC

We can use the HPC when we get to training, especially when running a few models with five-fold cross-validation and tuning hyperparameters. For now the data audit is mostly SQL in BigQuery and small CSVs, so there is no need to send a job to the HPC yet.

When we have a training table:

1. Check the cluster's Python modules, SLURM partition and resource limits.
2. Clone the private repo into the project workspace using the usual GitHub login. Put data and generated models in the approved storage location for the cluster.
3. Create an environment with the same Python and package versions we use locally. If the cluster supports Apptainer or another container runtime, we can check whether it can run our container there.
4. Run one small training job on a compute node. Record how long it took, how much memory it used and whether the results match the local run.
5. Use a batch job for larger model searches. Set the number of model workers to stay within the allocated CPUs, and save the results and logs as the jobs finish.

We will add the actual SLURM script once we know the available resources and have a working training command. No HPC job has been submitted yet.

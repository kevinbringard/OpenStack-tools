# nova-net-migration
Nova-Net to Neutron migration tools.


** USE AT YOUR OWN PERIL **

* This will assuredly need to be modified to suit your particular environment.
* Every effort has been made to ensure idempotence and sanity, but it goes without saying:
** This code is provided for reference only, and I take no responsibility for any damage you cause by using it.

A few points of particular interest:

* The compute_driver entries as well as the location of your RC file
* You'll need to setup your inventory or change the host group names to match your existing inventory.
* The RC file should have the SQL Passwords set in order for the setup-db script to work.
* I'd also recommend updating the location of the novenet2neutron code repo. I don't have any intention of removing it or otherwise breaking it, but hey, you never know.
* Be sure to specify the zone you want to migrate when you do the control plane migration. It gets uppity if you don't

Order of Operation:

* ansible-playbook -s prep-control-plane-migration.yml
* ansible-playbook -s run-control-plane-migration.yml -e "nova_zone=your target zone"
* ansible-playbook -s revert-mhvs.yml
* ansible-playbook -s prep-compute-nodes-migration.yml
* ansible-playbook -s run-compute-migration.yml
* ansible-playbook -s cleanup-bridges.yml

Happy migrating!

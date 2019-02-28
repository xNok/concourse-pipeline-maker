Utiliser le Concourse pipeline Maker et mettre à jour le pipeline manifest
===

## Objectif

The goal of this tool is to generate the pipeline manifest required by the ressource [concourse-pipeline-resource](https://github.com/concourse/concourse-pipeline-resource).

Additionally, it provide feature to improve the maintainability of your pipelines.

## Usage

> Structure /!\ Please be carefull with the syntax.

```md
CONCOURSE PIPELINE MAKER

Usage:
  cpm [--ifile <inputfile>] [--ofile <outputfile>] 
    [-p <text_to_search:replacement_text>...] [options]
  cpm <pipeline_name>... [--ifile <inputfile>] [--ofile <outputfile>] 
    [-p <text_to_search:replacement_text>...] [options]
  cpm -h | --help

Options:                         
  -i <inputfile>, --ifile <inputfile>       Path to the pipeline manifest. [default: pipelinemanifest.json]
  -o <outputfile>, --ofile <outputfile>     Path to the output folder. [default: pipelines_files]
  -p <text_to_search:replacement_text>      Search and replace operation applied before procssing the pipeline manifest.
                                            Very usefull when working locally.
  -c <sfolder>, --ci <sfolder>              When publishing pipelines in a repo make sure it is compatible with concourse/concourse-pipeline-resource [default: git-infra-res/]
Options-Flags:
  --cli                                     Generate the Fly command line for each pipeline
  --copy                                    Systematically copy the pipeline in the output directory.
  --debug                                   Set the log level to debug
  -h, --help                                Show the help screen.
```

## Définition des Pipelines

Pour definir les pipelines utiliser un objet JSON et definir les flag de la commande `fly` ainsi que leurs parametres.

Par example la commande fly suivante:

```sh
fly set-pipeline -t achat \
  -p service-dummy \
  -c ./consourse/pipelines/nonprod-services-pipeline.yml \
  --load-vars-from ./consourse/vars/vars-nonproduction.yml \
  --var "artifact_id=service-dummy"\
  --var "repo_id=service-dummy"
```

Se traduit dans le fichier de configuration de la manière suivante:

```json
{
  "configs": {},
  "templates": {},
  "pipelines":[
    {"-p": "service-dummy",
      "-c": "pipelines/services-pipeline.yml",
      "load-vars-from": "vars/vars-dev.yml",
      "var": {"artifact_id": "service-dummy", "repo_id": "service-dummy"}
    }
  ]
}
```

* La section `configs` peux être utiliser pour applicque une configurations à toutes les pipelines
* La section `template` peux etre utiliser pour créer des configuration et les applique une ou plusieur pipeline en utilisant la clef `-tpl`, `template`
* La section `pipelines` definit la configuration individuel de chaque pipeline

## Entrée accepter

* `pipeline`, `-p`: nom du pipeline
* `config`, `-c`: fichier de definition de la pipeline
* `load-vars-from`, `-l`: fichier de varibles (string or array)
* `var`, `-v`: tableau of variable key=value

* Arguments clasic de fly cli `set_pipeline`: 
    * `-p`, `pipeline`: nom du pipeline
    * `-c`, `config`:  fichier de definition de la pipeline
    * `-t`, `team`: nom de la team / org
    * `-l`, `load-vars-from`: fichier(s) de variables (string or array)
    * `-v`, `vars`: tableau of variable key=value

* Argument de templating
    * `-tpl`, `template`

* Argument de fusion de pipeline
    * `-m`, `merge`: ficher(s) yml `s fusioner avec le pipeline (string or array)

## Use case of cpm

I wanna generate and set pipelines locally:
```bash
# Process the pipeline manifest
cpm
# Process only 1 pipeline and give me the fly command to execute
cpm my_pipilene
# Process all pipeline and generate the fly_cli command line
cpm --cli
# Process all pipeline and copy all files in the output folder
cpm --copy
# My pipeline are in an other location and I use a generic name for it
cpm -p alias:path/to/the/folder
```

## Exemple de merge et de template dans les pipelines

L'exemple suivant démontre comment ajouter des fonctionalitè avec l'option de merge. Les fichier listé apres `-m` vont ajouter, les notifications slack, l'analyse static, les tests robots. De plus nous utilisont le mode templating pour rendre facile l'utilisation de cette configuration de pipeline.

```json
{
  "configs": {
    "-t": "team",
    "-l": "./pipelines_assets/vars-configs.yml",
    "-v": {
      "config": 1
    }
  },
  "templates": {
    "template": {
      "-c": "./pipelines_assets/pipeline.yml",
      "-l": "./pipelines_assets/vars-template.yml",
      "-v": {
        "test": 1,
        "tests": 2
      }
    }
  },
  "pipelines": [
    {
      "-p": "Test",
      "-tpl": "template",
      "-v": {
        "test": 7
      }
    }
  ]
}
```